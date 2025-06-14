import re 

from typing import Any, Dict, List, Optional, Union, Tuple
from db.db_connection import get_db_connection

class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass

def _validate_table_name(table_name: str) -> None:
    """
    Validate the table name using a regex pattern.

    Table Name Rules:
        - Must start with a letter or underscore
        - Can contain letters, numbers, and underscores
        - No special characters or spaces
    """
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        raise ValueError(
            f"Invalid table name: {table_name}. "
             "Must start with a letter or underscore, "
             "and contain only letters, numbers, and underscores."
        )
                         
                         
def execute_query(
    query: str,
    params: Optional[Union[Dict[str, Any]]] = None,
    fetch: bool = True,
    commit: bool = True
) -> Union[List[Dict[str, Any]], int, None]:
    """
    Execute a SQL query with optional parameters.
    Returns:
        - List of dictionaries if fetch is True
        - number of affected rows if commit is True and fetch is False  
        - None if not fetch or commit
    """
    if not query:
        raise ValueError("Query cannot be empty")

    conn = get_db_connection()

    if not conn:
        raise DatabaseError("Database connection failed")

    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if commit:
                conn.commit()
                
            if fetch:
                if query.strip().lower().startswith("select"):
                    rows = cur.fetchall()
                    return rows if rows else []
                return None
            else:
                return cur.rowcount

    except Exception as e:
        conn.rollback()
        raise DatabaseError(f"Query execution failed: {str(e)}")
    finally:
        conn.close()


def get_by_id(
    table: str, 
    row_id: Union[int, str]
) -> Optional[Dict[str, Any]]:
    """Get a single row by ID from the specified table.
    
    Args:
        table: Name of the table to query
        row_id: ID of the row to retrieve
    
    Returns:
        Dictionary of row data or None if not found
    """
    _validate_table_name(table)
    result = execute_query(
        f"SELECT * FROM {table} WHERE id = %s",
        (row_id,),
        fetch=True
    )
    return result[0] if result else None
    

def get_by_column(
    table: str,
    column: str,
    value: Any
) -> Optional[Dict[str, Any]]:
    """Get a single row by a specific column value.
    
    Args:
        table: Name of the table to query
        column: Column name to filter by
        value: Value to match in the specified column
    
    Returns:
        Dictionary of row data or None if not found
    """
    _validate_table_name(table)
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column):
        raise ValueError("Invalid column name")
    
    result = execute_query(
        f"SELECT * FROM {table} WHERE {column} = %s",
        (value,),
        fetch=True
    )
    return result[0] if result else None


def get_all(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get rows with filtering, sorting and pagination."""
    _validate_table_name(table)
    
    query = f"SELECT * FROM {table}"
    params = []
    
    # Handle filters
    if filters:
        conditions = [f"{k} = %s" for k in filters]
        query += " WHERE " + " AND ".join(conditions)
        params.extend(filters.values())
    
    # Handle ordering (validated)
    if order_by:
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', order_by):
            raise ValueError("Invalid order_by column")
        query += f" ORDER BY {order_by}"
    
    # Handle pagination (parameterized)
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)
        if offset is not None:
            query += " OFFSET %s"
            params.append(offset)
    
    return execute_query(query, params, fetch=True) or [] 


def insert_row(
    table: str,
    data: Dict[str, Any],
    returning: Optional[str] = "id"
) -> Optional[Dict[str, Any]]:
    """Insert a new row into the specified table.
    
    Args:
        table: Name of the table to insert into
        data: Dictionary of column-value pairs to insert
        returning: Column(s) to return after insertion (None for nothing)
                  Can be comma-separated columns or "*" for all columns
    
    Returns:
        Dictionary of returned columns or None if nothing requested
        
    Raises:
        ValueError: For invalid inputs
        DatabaseError: If insertion fails
    """
    _validate_table_name(table)
    
    if not data:
        raise ValueError("Data dictionary cannot be empty")
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    if returning:
        # Validate returning columns format
        if returning and any(not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col.strip()) for col in returning.split(',')):
            raise ValueError("Invalid returning column specification")

        query += f" RETURNING {returning}"
    
    try:
        result = execute_query(
            query, 
            tuple(data.values()), 
            fetch=bool(returning), 
            commit=True
        )
        return result[0] if result else None
    except Exception as e:
        raise DatabaseError(f"Failed to insert into {table}: {str(e)}")


def upsert_row(
    table:str,
    data: Dict[str, Any],
    conflict_column: str,
    update_columns: List[str],
    returning: Optional[str] = "id"
) -> Optional[Dict[str, Any]]:

    """
    Insert or update a row if it already exists in the table.

    Args:
        table: Name of the table to insert into.
        data: Row data.
        conflict_column: Column to check for conflicts.
        update_columns: Columns to update if conflict is found.
        returning: Optional columns to return.
    """

    _validate_table_name(table)
    if not data:
        raise ValueError("Data dictionary cannot be empty")

    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    updates= ', '.join([f'{col} = EXCLUDED.{col}' for col in update_columns])

    query = (
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_column}) DO UPDATE SET {updates} "
    )

    if returning:
        query += f" RETURNING {returning}"

    try: 
        result = execute_query(
            query,
            tuple(data.values()),
            fetch=bool(returning),
            commit=True
        )

        return result[0] if result else None
    
    except Exception as e:
        raise DatabaseError(f'Upsert failed for {table}: {str(e)}')


def update_by_id(
    table: str,
    row_id: Union[int, str],
    data: Dict[str, Any],
    returning: Optional[str] = "id"
) -> Optional[Dict[str, Any]]:
    """Update a table row by ID.
    
    Args:
        table: Table name to update
        row_id: ID of row to modify
        data: Dictionary of column-value pairs to update
        returning: Columns to return (None for nothing)
    
    Returns:
        Dictionary with returned columns or None
    
    Raises:
        ValueError: For invalid inputs
        DatabaseError: If update fails
    """
    _validate_table_name(table)
    
    if not data:
        raise ValueError("Update data cannot be empty")
    
    set_clause = ', '.join([f"{k} = %s" for k in data])
    query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
    params = list(data.values()) + [row_id]
    
    if returning:
        if returning and any(not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col.strip()) for col in returning.split(',')):
            raise ValueError("Invalid returning column specification")

        query += f" RETURNING {returning}"
    
    try:
        result = execute_query(
            query,
            tuple(params),
            fetch=bool(returning),
            commit=True
        )
        if returning:
            return result[0] if result else None
        else:
            return {"rows_updated": result}  # result is an integer
    
    except Exception as e:
        raise DatabaseError(f"Update failed for {table} ID {row_id}: {e}")  


def delete_by_id(
    table: str,
    row_id: Union[int, str],
    returning: Optional[str] = None
) -> Union[int, Optional[Dict[str, Any]]]:
    """Delete a row by ID from the specified table.
    
    Args:
        table: Name of the table to delete from
        row_id: ID of the row to delete
        returning: If specified, returns deleted data from these columns
    
    Returns:
        If returning=None: number of rows deleted (0 or 1)
        If returning specified: dictionary of deleted data or None if not found
    
    Raises:
        ValueError: For invalid inputs
        DatabaseError: If deletion fails
    """
    _validate_table_name(table)
    
    query = f"DELETE FROM {table} WHERE id = %s"
    params = (row_id,)
    
    if returning:
        if not re.match(r'^[\w,\s*]+$', returning):
            raise ValueError("Invalid returning columns specification")
        query += f" RETURNING {returning}"
    
    try:
        result = execute_query(
            query,
            params,
            fetch=bool(returning),
            commit=True
        )
        
        if returning:
            return result[0] if result else None
        return result
    except Exception as e:
        raise DatabaseError(f"Delete failed for {table} ID {row_id}: {e}")