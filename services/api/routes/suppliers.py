from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from tinydb.table import Document

from database import suppliers
from models import Country, SupplierCreate, SupplierResponse, SupplierStatus


router = APIRouter(prefix="/suppliers", tags=["suppliers"])


class SupplierRateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rate_per_shipment: float = Field(..., gt=0)


class SupplierStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: SupplierStatus


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_response(document: Document) -> SupplierResponse:
    return SupplierResponse(id=document.doc_id, **dict(document))


def _get_supplier_or_404(id: int) -> Document:
    document = suppliers.get(doc_id=id)
    if document is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return document


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier(payload: SupplierCreate) -> SupplierResponse:
    supplier_data = payload.model_dump(mode="json")
    supplier_data["updated_at"] = _utc_now_iso()
    supplier_id = suppliers.insert(supplier_data)
    return _to_response(_get_supplier_or_404(supplier_id))


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(
    country: Annotated[Country | None, Query()] = None,
    category: Annotated[str | None, Query(min_length=1)] = None,
) -> list[SupplierResponse]:
    documents = suppliers.all()

    if country is not None:
        documents = [
            document for document in documents if document.get("country") == country.value
        ]
    if category is not None:
        documents = [
            document
            for document in documents
            if category in document.get("categories", [])
        ]

    return [_to_response(document) for document in documents]


@router.get("/{id}", response_model=SupplierResponse)
def get_supplier(id: int) -> SupplierResponse:
    return _to_response(_get_supplier_or_404(id))


@router.patch("/{id}/rate", response_model=SupplierResponse)
def update_supplier_rate(id: int, payload: SupplierRateUpdate) -> SupplierResponse:
    _get_supplier_or_404(id)
    suppliers.update(
        {
            "rate_per_shipment": payload.rate_per_shipment,
            "updated_at": _utc_now_iso(),
        },
        doc_ids=[id],
    )
    return _to_response(_get_supplier_or_404(id))


@router.patch("/{id}/status", response_model=SupplierResponse)
def update_supplier_status(
    id: int,
    payload: SupplierStatusUpdate,
) -> SupplierResponse:
    _get_supplier_or_404(id)
    suppliers.update({"status": payload.status.value}, doc_ids=[id])
    return _to_response(_get_supplier_or_404(id))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(id: int) -> Response:
    _get_supplier_or_404(id)
    suppliers.remove(doc_ids=[id])
    return Response(status_code=status.HTTP_204_NO_CONTENT)