from fastapi import APIRouter, HTTPException
from config import settings
from database import contracts_collection
from bson import ObjectId
from app.service.gemini_analyse import analyze_contract
from database import analyses_collection

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
)

@router.get("/{contract_id}")
async def analyse_contract(contract_id: str):
    """
    Analyze a contract using AI and return insights.
    """

    if not settings.google_ai_api_key:
        raise HTTPException(status_code=500, detail="AI API key is not configured")

    contract = contracts_collection.find_one({"_id": ObjectId(contract_id)})

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.get("text_content"):
        raise HTTPException(status_code=400, detail="Contract has no text content")

    contracts_collection.update_one(
        {"_id": ObjectId(contract_id)}, {"$set": {"analysis_status": "in_progress"}}
    )

    result = await analyze_contract(contract_id, contract["text_content"])

    doc = result.model_dump()
    insert_result = analyses_collection.insert_one(doc)
    result.id = str(insert_result.inserted_id)

    contracts_collection.update_one(
        {"_id": ObjectId(contract_id)}, {"$set": {"analysis_status": "completed"}}
    )

    return {
        "message": "Contract analyzed successfully",
        "analysis": result.model_dump(),
        "id": result.id,
    }
