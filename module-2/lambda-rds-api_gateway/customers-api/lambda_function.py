
"""
Customers API Lambda Function
=============================

This Lambda exposes a REST-style API for managing customers.

Supported operations:

    POST    /customers
    GET     /customers
    GET     /customers?customer_id=CUST001
    PUT     /customers/{customer_id}
    DELETE  /customers/{customer_id}

Architecture
------------

API Gateway
    |
    v
Customers API Lambda
    |
    v
Generic Query Executor Lambda
    |
    v
AWS Secrets Manager
    |
    v
RDS MySQL

The Customers Lambda does NOT connect directly to MySQL.

All database access is delegated to the Generic Query Executor Lambda.
"""


import json
import os
import traceback
import boto3
import logging

from typing import Dict, Any


# =========================================================
# Logging Configuration
# =========================================================

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# =========================================================
# AWS Clients
# =========================================================

# Used to invoke the Generic Query Executor Lambda
lambda_client = boto3.client("lambda")


# =========================================================
# Configuration
# =========================================================

QUERY_EXECUTOR_FUNCTION = os.environ.get(
    "QUERY_EXECUTOR_FUNCTION",
    "generic-query-executor"
)

logger.info(
    f"Initialized with QUERY_EXECUTOR_FUNCTION: "
    f"{QUERY_EXECUTOR_FUNCTION}"
)


# =========================================================
# Helper: Invoke Generic Query Executor
# =========================================================

def invoke_query_executor(
    query: str,
    params: list = None,
    fetch: bool = True
) -> Dict[str, Any]:
    """
    Invoke the Generic Query Executor Lambda.

    Parameters
    ----------
    query:
        Parameterized SQL query.

    params:
        Values for %s placeholders.

    fetch:
        True  -> SELECT and return data
        False -> INSERT / UPDATE / DELETE

    Returns
    -------

    {
        "success": True,
        "data": [...],
        "rowcount": 1
    }

    OR

    {
        "success": False,
        "error": "..."
    }
    """

    logger.info(
        f"Invoking query executor: "
        f"function={QUERY_EXECUTOR_FUNCTION}, "
        f"query={query[:100]}, "
        f"params_count={len(params or [])}, "
        f"fetch={fetch}"
    )

    # -----------------------------------------------------
    # Payload sent to Generic Query Executor
    # -----------------------------------------------------

    payload = {
        "query": query,
        "params": params or [],
        "fetch": fetch
    }

    try:

        # -------------------------------------------------
        # Invoke Generic Query Executor synchronously
        # -------------------------------------------------

        response = lambda_client.invoke(
            FunctionName=QUERY_EXECUTOR_FUNCTION,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        logger.info(
            f"Query executor invocation completed. "
            f"Status code: {response.get('StatusCode')}"
        )

        # -------------------------------------------------
        # Read Lambda response
        # -------------------------------------------------

        response_payload = json.loads(
            response["Payload"].read()
        )

        # -------------------------------------------------
        # Generic Query Executor may return:
        #
        # {
        #     "statusCode": 200,
        #     "body": "..."
        # }
        #
        # So handle that case.
        # -------------------------------------------------

        if isinstance(
            response_payload.get("body"),
            str
        ):

            result = json.loads(
                response_payload["body"]
            )

        else:

            result = response_payload

        # -------------------------------------------------
        # Log result
        # -------------------------------------------------

        if result.get("success"):

            if fetch:
                data = result.get("data") or []

                logger.info(
                    f"Query executed successfully. "
                    f"Row count: {result.get('rowcount')}, "
                    f"Data count: {len(data)}"
                )

            else:
                logger.info(
                    f"Query executed successfully. "
                    f"Rows affected: {result.get('rowcount')}"
                )

        else:

            logger.error(
                f"Query execution failed: "
                f"{result.get('error')}"
            )

        return result

    except Exception as e:

        logger.error(
            f"Failed to invoke query executor. "
            f"Error: {str(e)}, "
            f"Type: {type(e).__name__}, "
            f"Trace: {traceback.format_exc()}"
        )

        return {
            "success": False,
            "error": (
                f"Lambda invocation failed: {str(e)}"
            )
        }


# =========================================================
# POST /customers
# =========================================================

def create_customer(
    event_body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a new customer.

    Request:

    POST /customers

    Body:

    {
        "customer_id": "CUST001",
        "customer_name": "John Doe",
        "email": "john@example.com",
        "city": "New York",
        "state": "NY"
    }
    """

    logger.info(
        f"Creating customer. "
        f"customer_id={event_body.get('customer_id')}, "
        f"email={event_body.get('email')}"
    )

    # -----------------------------------------------------
    # Validate required fields
    # -----------------------------------------------------

    required_fields = [
        "customer_id",
        "customer_name",
        "email"
    ]

    for field in required_fields:

        if field not in event_body:

            logger.warning(
                f"Missing required field: {field}"
            )

            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": (
                        f"Missing required field: {field}"
                    )
                })
            }

    # -----------------------------------------------------
    # MySQL INSERT
    #
    # IMPORTANT:
    # MySQL version does NOT use RETURNING.
    # -----------------------------------------------------

    insert_query = """
        INSERT INTO demo.customers
        (
            customer_id,
            customer_name,
            email,
            city,
            state,
            created_at
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            CURRENT_TIMESTAMP
        )
    """

    params = [
        event_body["customer_id"],
        event_body["customer_name"],
        event_body["email"],
        event_body.get("city"),
        event_body.get("state")
    ]

    # -----------------------------------------------------
    # Execute INSERT
    # -----------------------------------------------------

    insert_result = invoke_query_executor(
        insert_query,
        params,
        fetch=False
    )

    if not insert_result.get("success"):

        logger.error(
            f"Failed to create customer. "
            f"Error: {insert_result.get('error')}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": insert_result.get(
                    "error",
                    "Failed to create customer"
                )
            })
        }

    # -----------------------------------------------------
    # MySQL does not use RETURNING.
    #
    # Fetch the newly created customer separately.
    # -----------------------------------------------------

    select_query = """
        SELECT
            customer_id,
            customer_name,
            email,
            city,
            state,
            created_at
        FROM demo.customers
        WHERE customer_id = %s
    """

    select_result = invoke_query_executor(
        select_query,
        [event_body["customer_id"]],
        fetch=True
    )

    if not select_result.get("success"):

        logger.warning(
            "Customer was created but could not "
            "be fetched after INSERT."
        )

        return {
            "statusCode": 201,
            "body": json.dumps({
                "success": True,
                "message": (
                    "Customer created successfully"
                )
            })
        }

    data = select_result.get(
        "data",
        []
    )

    return {
        "statusCode": 201,
        "body": json.dumps({
            "success": True,
            "message": (
                "Customer created successfully"
            ),
            "data": (
                data[0]
                if data
                else None
            )
        }, default=str)
    }


# =========================================================
# GET /customers
# =========================================================

def get_customers(
    query_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fetch customers.

    GET /customers

    Returns all customers.

    GET /customers?customer_id=CUST001

    Returns one customer.
    """

    customer_id = query_params.get(
        "customer_id"
    )

    logger.info(
        f"Fetching customers. "
        f"customer_id={customer_id}"
    )

    # -----------------------------------------------------
    # Fetch single customer
    # -----------------------------------------------------

    if customer_id:

        query = """
            SELECT
                customer_id,
                customer_name,
                email,
                city,
                state,
                created_at
            FROM demo.customers
            WHERE customer_id = %s
        """

        params = [
            customer_id
        ]

    # -----------------------------------------------------
    # Fetch all customers
    # -----------------------------------------------------

    else:

        query = """
            SELECT
                customer_id,
                customer_name,
                email,
                city,
                state,
                created_at
            FROM demo.customers
            ORDER BY created_at DESC
        """

        params = []

    # -----------------------------------------------------
    # Execute SELECT
    # -----------------------------------------------------

    result = invoke_query_executor(
        query,
        params,
        fetch=True
    )

    if result.get("success"):

        data = result.get(
            "data",
            []
        )

        logger.info(
            f"Customers fetched successfully. "
            f"Count={len(data)}"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "data": data,
                "count": len(data)
            }, default=str)
        }

    logger.error(
        f"Failed to fetch customers. "
        f"Error={result.get('error')}"
    )

    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": result.get(
                "error",
                "Unknown error"
            )
        })
    }


# =========================================================
# PUT /customers/{customer_id}
# =========================================================

def update_customer(
    customer_id: str,
    event_body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates an existing customer.

    PUT /customers/{customer_id}

    Example:

    PUT /customers/CUST001

    Body:

    {
        "email": "newemail@example.com",
        "city": "Boston"
    }

    Only supplied fields are updated.
    """

    logger.info(
        f"Updating customer. "
        f"customer_id={customer_id}, "
        f"fields={list(event_body.keys())}"
    )

    # -----------------------------------------------------
    # Validate customer ID
    # -----------------------------------------------------

    if not customer_id:

        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "customer_id is required"
            })
        }

    # -----------------------------------------------------
    # Build UPDATE fields
    # -----------------------------------------------------

    update_fields = []
    params = []

    allowed_fields = [
        "customer_name",
        "email",
        "city",
        "state"
    ]

    for field in allowed_fields:

        if field in event_body:

            update_fields.append(
                f"{field} = %s"
            )

            params.append(
                event_body[field]
            )

    # -----------------------------------------------------
    # No fields provided
    # -----------------------------------------------------

    if not update_fields:

        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "No fields to update"
            })
        }

    # customer_id is the final parameter
    params.append(
        customer_id
    )

    # -----------------------------------------------------
    # MySQL UPDATE
    #
    # IMPORTANT:
    # No RETURNING clause.
    # -----------------------------------------------------

    update_query = f"""
        UPDATE demo.customers
        SET {', '.join(update_fields)}
        WHERE customer_id = %s
    """

    logger.info(
        f"Executing UPDATE. "
        f"customer_id={customer_id}"
    )

    # -----------------------------------------------------
    # Execute UPDATE
    # -----------------------------------------------------

    result = invoke_query_executor(
        update_query,
        params,
        fetch=False
    )

    if not result.get("success"):

        logger.error(
            f"Failed to update customer. "
            f"Error={result.get('error')}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": result.get(
                    "error",
                    "Failed to update customer"
                )
            })
        }

    # -----------------------------------------------------
    # Check whether customer existed
    # -----------------------------------------------------

    if result.get(
        "rowcount",
        0
    ) == 0:

        logger.warning(
            f"Customer not found. "
            f"customer_id={customer_id}"
        )

        return {
            "statusCode": 404,
            "body": json.dumps({
                "success": False,
                "error": (
                    f"Customer {customer_id} "
                    f"not found"
                )
            })
        }

    # -----------------------------------------------------
    # Fetch updated customer
    # -----------------------------------------------------

    select_query = """
        SELECT
            customer_id,
            customer_name,
            email,
            city,
            state,
            created_at
        FROM demo.customers
        WHERE customer_id = %s
    """

    select_result = invoke_query_executor(
        select_query,
        [customer_id],
        fetch=True
    )

    if not select_result.get("success"):

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": (
                    "Customer updated successfully"
                )
            })
        }

    data = select_result.get(
        "data",
        []
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "success": True,
            "message": (
                "Customer updated successfully"
            ),
            "data": (
                data[0]
                if data
                else None
            )
        }, default=str)
    }


# =========================================================
# DELETE /customers/{customer_id}
# =========================================================

def delete_customer(
    customer_id: str
) -> Dict[str, Any]:
    """
    Deletes a customer.

    Before deleting, checks whether the customer
    has any existing orders.

    If orders exist, deletion is blocked.
    """

    logger.info(
        f"Deleting customer. "
        f"customer_id={customer_id}"
    )

    # -----------------------------------------------------
    # Validate customer ID
    # -----------------------------------------------------

    if not customer_id:

        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": "customer_id is required"
            })
        }

    # -----------------------------------------------------
    # Check existing orders
    # -----------------------------------------------------

    check_query = """
        SELECT
            COUNT(*) AS order_count
        FROM demo.orders
        WHERE customer_id = %s
    """

    check_result = invoke_query_executor(
        check_query,
        [customer_id],
        fetch=True
    )

    # -----------------------------------------------------
    # If order check fails,
    # DO NOT delete the customer.
    # -----------------------------------------------------

    if not check_result.get("success"):

        logger.error(
            f"Order check failed. "
            f"Error={check_result.get('error')}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": (
                    "Unable to verify customer orders"
                )
            })
        }

    # -----------------------------------------------------
    # Get order count
    # -----------------------------------------------------

    order_data = check_result.get(
        "data",
        []
    )

    order_count = 0

    if order_data:

        order_count = int(
            order_data[0].get(
                "order_count",
                0
            )
        )

    logger.info(
        f"Customer {customer_id} "
        f"has {order_count} orders."
    )

    # -----------------------------------------------------
    # Block deletion if orders exist
    # -----------------------------------------------------

    if order_count > 0:

        logger.warning(
            f"Delete blocked. "
            f"Customer has existing orders. "
            f"customer_id={customer_id}"
        )

        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": (
                    "Cannot delete customer "
                    "with existing orders"
                )
            })
        }

    # -----------------------------------------------------
    # Delete customer
    # -----------------------------------------------------

    delete_query = """
        DELETE FROM demo.customers
        WHERE customer_id = %s
    """

    logger.info(
        f"Executing DELETE. "
        f"customer_id={customer_id}"
    )

    result = invoke_query_executor(
        delete_query,
        [customer_id],
        fetch=False
    )

    if not result.get("success"):

        logger.error(
            f"Failed to delete customer. "
            f"Error={result.get('error')}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": result.get(
                    "error",
                    "Failed to delete customer"
                )
            })
        }

    # -----------------------------------------------------
    # Customer didn't exist
    # -----------------------------------------------------

    if result.get(
        "rowcount",
        0
    ) == 0:

        return {
            "statusCode": 404,
            "body": json.dumps({
                "success": False,
                "error": (
                    f"Customer {customer_id} "
                    f"not found"
                )
            })
        }

    # -----------------------------------------------------
    # Success
    # -----------------------------------------------------

    logger.info(
        f"Customer deleted successfully. "
        f"customer_id={customer_id}"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "success": True,
            "message": (
                f"Customer {customer_id} "
                f"deleted successfully"
            )
        })
    }


# =========================================================
# Lambda Entry Point
# =========================================================

def lambda_handler(
    event: Dict[str, Any],
    context: Any
) -> Dict[str, Any]:
    """
    AWS Lambda entry point.

    Supports:

    API Gateway REST API:
        event["httpMethod"]

    API Gateway HTTP API:
        event["requestContext"]["http"]["method"]

    Path parameters:
        /customers/{customer_id}

    Query parameters:
        /customers?customer_id=CUST001
    """

    logger.info(
        "Customers API Lambda invocation started."
    )

    try:

        # -------------------------------------------------
        # Determine HTTP method
        # -------------------------------------------------

        http_method = event.get(
            "httpMethod",
            event.get(
                "requestContext",
                {}
            ).get(
                "http",
                {}
            ).get(
                "method"
            )
        )

        # -------------------------------------------------
        # Read path parameters
        # -------------------------------------------------

        path_parameters = (
            event.get("pathParameters")
            or {}
        )

        # -------------------------------------------------
        # Read query parameters
        # -------------------------------------------------

        query_parameters = (
            event.get(
                "queryStringParameters"
            )
            or {}
        )

        logger.info(
            f"Request received. "
            f"method={http_method}, "
            f"path={event.get('path')}, "
            f"path_parameters={path_parameters}, "
            f"query_parameters={query_parameters}"
        )

        # -------------------------------------------------
        # Parse request body
        # -------------------------------------------------

        body = {}

        if event.get("body"):

            try:

                if isinstance(
                    event["body"],
                    str
                ):

                    body = json.loads(
                        event["body"]
                    )

                else:

                    body = event["body"]

                logger.info(
                    f"Request body parsed. "
                    f"keys={list(body.keys())}"
                )

            except json.JSONDecodeError:

                logger.error(
                    "Invalid JSON request body."
                )

                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type":
                            "application/json",
                        "Access-Control-Allow-Origin":
                            "*"
                    },
                    "body": json.dumps({
                        "success": False,
                        "error": (
                            "Invalid JSON in "
                            "request body"
                        )
                    })
                }

        # =================================================
        # Route request
        # =================================================

        if http_method == "POST":

            response = create_customer(
                body
            )

        elif http_method == "GET":

            response = get_customers(
                query_parameters
            )

        elif http_method == "PUT":

            # First look for customer_id
            # in path parameter.
            #
            # Then query parameter.

            customer_id = (
                path_parameters.get(
                    "customer_id"
                )
                or
                query_parameters.get(
                    "customer_id"
                )
                or
                query_parameters.get(
                    "id"
                )
            )

            response = update_customer(
                customer_id,
                body
            )

        elif http_method == "DELETE":

            customer_id = (
                path_parameters.get(
                    "customer_id"
                )
                or
                query_parameters.get(
                    "customer_id"
                )
                or
                query_parameters.get(
                    "id"
                )
            )

            response = delete_customer(
                customer_id
            )

        elif http_method == "OPTIONS":

            response = {
                "statusCode": 200,
                "body": json.dumps({
                    "success": True
                })
            }

        else:

            logger.warning(
                f"Unsupported HTTP method: "
                f"{http_method}"
            )

            response = {
                "statusCode": 405,
                "body": json.dumps({
                    "success": False,
                    "error": (
                        f"Method {http_method} "
                        f"not allowed"
                    )
                })
            }

        # =================================================
        # CORS Headers
        # =================================================

        response.setdefault(
            "headers",
            {}
        )

        response["headers"].update({

            "Content-Type":
                "application/json",

            "Access-Control-Allow-Origin":
                "*",

            "Access-Control-Allow-Methods":
                "GET, POST, PUT, DELETE, OPTIONS",

            "Access-Control-Allow-Headers":
                "Content-Type"
        })

        logger.info(
            f"Lambda invocation completed. "
            f"status_code={response.get('statusCode')}"
        )

        return response

    # =====================================================
    # Global Exception Handler
    # =====================================================

    except Exception as e:

        logger.error(
            f"Unhandled exception in "
            f"lambda_handler. "
            f"Error={str(e)}, "
            f"Type={type(e).__name__}, "
            f"Trace={traceback.format_exc()}"
        )

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type":
                    "application/json",

                "Access-Control-Allow-Origin":
                    "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }

