from __future__ import annotations

import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.bank import get_new_transactions, import_csv_data, ExternalServiceError

router = APIRouter(
    prefix="/bank",
    tags=["Bank Integration"],
    responses={404: {"description": "Not found"}},
)


@router.post("/update_from_bank", status_code=status.HTTP_200_OK)
def update_from_bank(db: Session = Depends(get_db)):
    """
    Connect to the bank API, fetch new transactions, insert them,
    and update account balances.

    Returns a mapping of account name -> number of inserted transactions for this run.
    """
    try:
        new_transactions = get_new_transactions(db)
    except ExternalServiceError as e:
        # Upstream banking API is failing/unavailable
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return {
        "message": "Bank update completed.",
        "inserted": new_transactions,
    }


@router.post("/import_csv", status_code=status.HTTP_200_OK)
async def import_csv(
    file: UploadFile = File(...),
    holder_name: str = Form(..., description="Account holder name"),
    parser_type: str = Form("dkb", description="CSV parser type (e.g., 'dkb')"),
    db: Session = Depends(get_db)
):
    """
    Import transactions from a CSV bank statement file.
    
    Supports multiple bank formats through the parser_type parameter.
    Uses the same duplicate detection and import pipeline as the live bank integration.
    
    Returns a mapping of account name -> number of inserted transactions for this import.
    """
    try:
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Convert to file-like object for parser
        file_obj = io.BytesIO(content)
        
        # Import using CSV parser
        inserted_counts = import_csv_data(
            db=db,
            file_obj=file_obj,
            parser_type=parser_type,
            holder_name=holder_name
        )
        
        return {
            "message": "CSV import completed.",
            "inserted": inserted_counts,
            "parser_used": parser_type,
            "filename": file.filename
        }
        
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during CSV import: {str(e)}"
        )
