from fastapi import APIRouter, Query
from tools.azure_resource_graph import get_resources_by_tags, get_tag_values

router = APIRouter()

@router.get("/cloud-resources/tags")
async def tag_values():
    """Returns distinct values for each standard tag key."""
    return await get_tag_values()

@router.get("/cloud-resources/filter")
async def filter_by_tags(
    project: str | None = Query(None),
    environment: str | None = Query(None),
    owner: str | None = Query(None),
    application: str | None = Query(None),
):
    filters = {k: v for k, v in {
        "Project": project, "Environment": environment,
        "Owner": owner, "Application": application,
    }.items() if v}
    return await get_resources_by_tags(filters)