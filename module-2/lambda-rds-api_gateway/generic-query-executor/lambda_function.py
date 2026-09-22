"""
Generic Query Executor Lambda - MySQL Version
==============================================

This Lambda function acts as a database access layer for application Lambdas.

Architecture
------------
Business Lambda
      |
      v
Generic Query Executor Lambda
      |
      v
AWS Secrets Manager
      |
      v
Amazon RDS for MySQL

The Lambda:
- Retrieves MySQL credentials from AWS Secrets Manager
- Caches credentials during warm Lambda invocations
- Maintains a connection pool during warm Lambda invocations
- Executes parameterized SQL queries
- Commits successful transactions
- Rolls back failed transactions
"""

import json
import os
import boto3
import logging
import traceback

from botocore.exceptions import ClientError
import pymysql
from pymysql import cursors
from typing import Dict, Any, Optional


# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# Global State
# ---------------------------------------------------------

# MySQL connection pool.
#
# Lambda execution environments can be reused across
# multiple invocations. Connections stored here can
# therefore potentially be reused.
connection_pool = []

# Cached Secrets Manager credentials.
cached_credentials = None


# ---------------------------------------------------------
# Secrets Manager Integration
# ---------------------------------------------------------

def get_secret(secret_name: str) -> Dict[str, Any]:
    """
    Retrieve MySQL database credentials from AWS Secrets Manager.

    Expected secret format:

    {
        "username": "admin",
        "password": "password",
        "host": "mydb.xxxxx.rds.amazonaws.com",
        "port": 3306,
        "dbname": "mydatabase"
    }

    Credentials are cached in the Lambda execution environment
    to avoid calling Secrets Manager for every invocation.
    """

    global cached_credentials

    # -----------------------------------------------------
    # Return cached credentials if already available
    # -----------------------------------------------------
    secret_name = "dev/genai/mysql1"
    if cached_credentials:
        logger.info(
            f"Using cached credentials for secret from AWS: {secret_name}"
        )
        return cached_credentials

    region = os.environ.get("AWS_REGION", "ap-south-1")

    logger.info(
        f"Fetching credentials from Secrets Manager, "
        f"secret: {secret_name}, region: {region}"
    )

    # -----------------------------------------------------
    # Create Secrets Manager client
    # -----------------------------------------------------

    session = boto3.session.Session()

    client = session.client(
        service_name="secretsmanager",
        region_name=region
    )

    try:

        response = client.get_secret_value(
            SecretId=secret_name
        )

        logger.info(
            f"Successfully retrieved secret: {secret_name}"
        )

    except ClientError as e:

        error_code = e.response["Error"]["Code"]

        logger.error(
            f"Failed to retrieve secret: {secret_name}, "
            f"error_code: {error_code}, "
            f"error: {str(e)}, "
            f"trace: {traceback.format_exc()}"
        )

        if error_code == "DecryptionFailureException":
            raise Exception(
                "Secrets Manager cannot decrypt the secret"
            )

        elif error_code == "InternalServiceErrorException":
            raise Exception(
                "Secrets Manager internal service error"
            )

        elif error_code == "InvalidParameterException":
            raise Exception(
                "Invalid parameter while fetching secret"
            )

        elif error_code == "InvalidRequestException":
            raise Exception(
                "Invalid request to Secrets Manager"
            )

        elif error_code == "ResourceNotFoundException":
            raise Exception(
                f"Secret '{secret_name}' not found"
            )

        elif error_code == "AccessDeniedException":
            raise Exception(
                "Lambda does not have permission to read the secret"
            )

        else:
            raise Exception(
                f"Unexpected Secrets Manager error: {str(e)}"
            )

    # -----------------------------------------------------
    # Parse SecretString
    # -----------------------------------------------------

    if "SecretString" in response:

        secret = json.loads(
            response["SecretString"]
        )

        cached_credentials = secret

        logger.info(
            f"Secret parsed and cached: {secret_name}"
        )

        return secret

    logger.error(
        f"Unsupported binary secret format: {secret_name}"
    )

    raise Exception(
        "Unsupported secret format (binary secret)"
    )


# ---------------------------------------------------------
# Create MySQL Connection
# ---------------------------------------------------------

def create_db_connection():
    """
    Create a new MySQL database connection.

    Connection credentials are retrieved from Secrets Manager.
    """

    # -----------------------------------------------------
    # Secret name
    # -----------------------------------------------------

    secret_name = os.environ.get("DB_SECRET_NAME")

    if not secret_name:

        logger.error(
            "DB_SECRET_NAME environment variable not set"
        )

        raise Exception(
            "DB_SECRET_NAME environment variable is not set"
        )

    # -----------------------------------------------------
    # Get credentials
    # -----------------------------------------------------

    credentials = get_secret(secret_name)

    db_host = credentials.get(
        "host",
        os.environ.get("DB_HOST")
    )

    db_name = credentials.get(
        "dbname",
        os.environ.get("DB_NAME")
    )

    db_user = credentials.get(
        "username",
        os.environ.get("DB_USER")
    )

    db_password = credentials.get(
        "password"
    )

    db_port = int(
        credentials.get(
            "port",
            os.environ.get("DB_PORT", 3306)
        )
    )

    # -----------------------------------------------------
    # Validate required credentials
    # -----------------------------------------------------

    if not db_host:
        raise Exception("Database host is missing")

    if not db_user:
        raise Exception("Database username is missing")

    if not db_password:
        raise Exception(
            "Database password is missing from Secrets Manager"
        )

    logger.info(
        f"Creating MySQL connection, "
        f"host: {db_host}, "
        f"database: {db_name}, "
        f"user: {db_user}, "
        f"port: {db_port}"
    )

    try:

        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,

            # Return rows as dictionaries:
            # {"customer_id": 1, "name": "John"}
            cursorclass=cursors.DictCursor,

            # Automatically detect stale connections
            autocommit=False,

            # Connection timeout
            connect_timeout=10
        )

        logger.info(
            "MySQL connection created successfully"
        )

        return connection

    except pymysql.MySQLError as e:

        logger.error(
            f"Failed to connect to MySQL, "
            f"host: {db_host}, "
            f"database: {db_name}, "
            f"error: {str(e)}, "
            f"type: {type(e).__name__}, "
            f"trace: {traceback.format_exc()}"
        )

        raise


# ---------------------------------------------------------
# Database Connection Pool Management
# ---------------------------------------------------------

def get_db_connection():
    """
    Acquire a MySQL connection.

    A simple connection pool is maintained inside the
    Lambda execution environment.
    """

    global connection_pool

    logger.info(
        f"Current connection pool size: "
        f"{len(connection_pool)}"
    )

    # -----------------------------------------------------
    # Try to reuse an existing connection
    # -----------------------------------------------------

    while connection_pool:

        conn = connection_pool.pop()

        try:

            # Check whether connection is still alive.
            conn.ping(reconnect=True)

            logger.info(
                f"Reusing existing MySQL connection, "
                f"connection_id: {id(conn)}"
            )

            return conn

        except pymysql.MySQLError:

            logger.warning(
                "Existing MySQL connection is invalid. "
                "Creating a new connection."
            )

            try:
                conn.close()
            except Exception:
                pass

    # -----------------------------------------------------
    # No usable connection available
    # -----------------------------------------------------

    logger.info(
        "No reusable connection available. "
        "Creating a new MySQL connection."
    )

    return create_db_connection()


def return_db_connection(conn):
    """
    Return a MySQL connection to the connection pool.

    Maximum pool size is controlled by DB_POOL_MAX_SIZE.
    """

    global connection_pool

    if not conn:
        return

    max_pool_size = int(
        os.environ.get(
            "DB_POOL_MAX_SIZE",
            "5"
        )
    )

    try:

        # Make sure the connection is still alive.
        conn.ping(reconnect=True)

        if len(connection_pool) < max_pool_size:

            connection_pool.append(conn)

            logger.info(
                f"MySQL connection returned to pool, "
                f"connection_id: {id(conn)}, "
                f"pool_size: {len(connection_pool)}"
            )

        else:

            logger.info(
                "Connection pool is full. "
                "Closing connection."
            )

            conn.close()

    except pymysql.MySQLError as e:

        logger.warning(
            f"Failed to return connection to pool. "
            f"Closing connection. Error: {str(e)}"
        )

        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------
# Core Query Execution Logic
# ---------------------------------------------------------

def execute_query(
    query: str,
    params: Optional[tuple] = None,
    fetch: bool = True
) -> Dict[str, Any]:
    """
    Execute a SQL query against MySQL.

    Examples:

    SELECT:
        SELECT * FROM customers WHERE customer_id = %s

    INSERT:
        INSERT INTO customers(name) VALUES (%s)

    UPDATE:
        UPDATE customers SET name = %s WHERE customer_id = %s

    DELETE:
        DELETE FROM customers WHERE customer_id = %s

    Parameters are passed separately to prevent SQL injection.
    """

    conn = None
    cursor = None

    logger.info(
        f"Executing query: {query}, "
        f"params: {params}, "
        f"fetch: {fetch}"
    )

    try:

        # -------------------------------------------------
        # Acquire database connection
        # -------------------------------------------------

        conn = get_db_connection()

        # -------------------------------------------------
        # Create cursor
        # -------------------------------------------------

        cursor = conn.cursor()

        logger.info(
            f"Executing SQL statement: {query}"
        )

        # -------------------------------------------------
        # Execute parameterized query
        # -------------------------------------------------

        cursor.execute(
            query,
            params
        )

        logger.info(
            f"SQL statement executed successfully, "
            f"rowcount: {cursor.rowcount}"
        )

        result = {
            "success": True,
            "rowcount": cursor.rowcount
        }

        # -------------------------------------------------
        # SELECT query
        # -------------------------------------------------

        if fetch:

            rows = cursor.fetchall()

            result["data"] = rows

            logger.info(
                f"Query results fetched, "
                f"rowcount: {cursor.rowcount}, "
                f"result_count: {len(rows)}"
            )

        else:

            result["data"] = None

        # -------------------------------------------------
        # Commit transaction
        # -------------------------------------------------

        conn.commit()

        logger.info(
            f"Transaction committed, "
            f"rowcount: {cursor.rowcount}"
        )

        return result

    # -----------------------------------------------------
    # MySQL database error
    # -----------------------------------------------------

    except pymysql.MySQLError as e:

        if conn:

            try:
                conn.rollback()

                logger.info(
                    f"Transaction rolled back, "
                    f"query: {query}"
                )

            except Exception:
                pass

        logger.error(
            f"MySQL database error, "
            f"query: {query}, "
            f"params: {params}, "
            f"error: {str(e)}, "
            f"error_code: {getattr(e, 'args', [None])[0]}, "
            f"type: {type(e).__name__}, "
            f"trace: {traceback.format_exc()}"
        )

        return {
            "success": False,
            "error": str(e),
            "error_code": (
                e.args[0]
                if e.args
                else None
            )
        }

    # -----------------------------------------------------
    # Unexpected error
    # -----------------------------------------------------

    except Exception as e:

        if conn:

            try:
                conn.rollback()
            except Exception:
                pass

        logger.error(
            f"Unexpected error during query execution, "
            f"query: {query}, "
            f"params: {params}, "
            f"error: {str(e)}, "
            f"type: {type(e).__name__}, "
            f"trace: {traceback.format_exc()}"
        )

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        # -------------------------------------------------
        # Close cursor
        # -------------------------------------------------

        if cursor:

            try:
                cursor.close()

                logger.info(
                    f"Cursor closed for query: {query}"
                )

            except Exception:
                pass

        # -------------------------------------------------
        # Return connection to pool
        # -------------------------------------------------

        if conn:

            return_db_connection(conn)


# ---------------------------------------------------------
# Lambda Entry Point
# ---------------------------------------------------------

def lambda_handler(
    event: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:

    """
    AWS Lambda entry point.

    Supports both:

    1. Direct Lambda invocation

    {
        "query": "SELECT * FROM customers WHERE customer_id = %s",
        "params": ["CUST001"],
        "fetch": true
    }


    2. API Gateway invocation

    {
        "body": "{\"query\":\"SELECT * FROM customers WHERE customer_id = %s\", \"params\":[\"CUST001\"]}"
    }
    """

    logger.info(
        "Lambda invocation started"
    )

    try:

        # -------------------------------------------------
        # Parse request body
        # -------------------------------------------------

        if isinstance(
            event.get("body"),
            str
        ):

            logger.info(
                "Parsing API Gateway request body"
            )

            body = json.loads(
                event["body"]
            )

        else:

            logger.info(
                "Using direct Lambda invocation payload"
            )

            body = event

        # -------------------------------------------------
        # Extract request parameters
        # -------------------------------------------------

        query = body.get("query")

        params = body.get(
            "params"
        )

        fetch = body.get(
            "fetch",
            True
        )

        logger.info(
            f"Request parsed, "
            f"query: {query}, "
            f"params: {params}, "
            f"fetch: {fetch}"
        )

        # -------------------------------------------------
        # Validate query
        # -------------------------------------------------

        if not query:

            logger.warning(
                "Query validation failed - query is required"
            )

            return {
                "statusCode": 400,

                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },

                "body": json.dumps({
                    "success": False,
                    "error": "Query is required"
                })
            }

        # -------------------------------------------------
        # Convert params list to tuple
        # -------------------------------------------------

        if params and isinstance(
            params,
            list
        ):

            params = tuple(params)

            logger.info(
                f"Converted params list to tuple, "
                f"param_count: {len(params)}"
            )

        # -------------------------------------------------
        # Execute SQL query
        # -------------------------------------------------

        result = execute_query(
            query,
            params,
            fetch
        )

        # -------------------------------------------------
        # HTTP status
        # -------------------------------------------------

        status_code = (
            200
            if result["success"]
            else 500
        )

        logger.info(
            f"Lambda invocation completed, "
            f"status_code: {status_code}, "
            f"success: {result['success']}, "
            f"rowcount: {result.get('rowcount')}"
        )

        # -------------------------------------------------
        # API Gateway response
        # -------------------------------------------------

        return {

            "statusCode": status_code,

            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },

            "body": json.dumps(
                result,
                default=str
            )
        }

    # -----------------------------------------------------
    # Invalid JSON
    # -----------------------------------------------------

    except json.JSONDecodeError as e:

        logger.error(
            f"JSON decode error: {str(e)}, "
            f"trace: {traceback.format_exc()}"
        )

        return {

            "statusCode": 400,

            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },

            "body": json.dumps({

                "success": False,

                "error":
                    f"Invalid JSON payload: {str(e)}"

            })
        }

    # -----------------------------------------------------
    # Unexpected Lambda error
    # -----------------------------------------------------

    except Exception as e:

        logger.error(
            f"Unhandled exception in lambda_handler, "
            f"error: {str(e)}, "
            f"type: {type(e).__name__}, "
            f"trace: {traceback.format_exc()}"
        )

        return {

            "statusCode": 500,

            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },

            "body": json.dumps({

                "success": False,

                "error": str(e)

            })
        }