from datetime import datetime, timedelta, timezone

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContainerClient,
    ContentSettings,
    generate_blob_sas,
)

from pipeline.config import AUDIO_CONTENT_TYPE, Settings


def get_container(settings: Settings, create: bool = True) -> ContainerClient:
    service = BlobServiceClient.from_connection_string(settings.storage_connection_string)
    container = service.get_container_client(settings.storage_container)
    if create and not container.exists():
        container.create_container()
    return container


def build_blob_path(workflow: str, lesson_id: str, created_at: datetime) -> str:
    return f"lessons/{workflow}/{created_at:%Y}/{created_at:%m}/{lesson_id}.mp3"


def upload_audio(container: ContainerClient, blob_path: str, audio: bytes) -> str:
    blob = container.get_blob_client(blob_path)
    blob.upload_blob(
        audio,
        overwrite=False,
        content_settings=ContentSettings(
            content_type=AUDIO_CONTENT_TYPE,
            cache_control="public, max-age=31536000, immutable",
        ),
    )
    return blob.url


def blob_size(container: ContainerClient, blob_path: str) -> int:
    return container.get_blob_client(blob_path).get_blob_properties().size


def delete_audio(container: ContainerClient, blob_path: str) -> bool:
    try:
        container.get_blob_client(blob_path).delete_blob()
        return True
    except ResourceNotFoundError:
        return False


def is_public(container: ContainerClient) -> bool:
    return container.get_container_properties().public_access is not None


def signed_read_url(container: ContainerClient, settings: Settings, blob_path: str) -> str:
    """Time-limited read link, needed because student storage accounts usually block anonymous access."""
    blob = container.get_blob_client(blob_path)
    credential = container.credential
    sas = generate_blob_sas(
        account_name=blob.account_name,
        container_name=container.container_name,
        blob_name=blob_path,
        account_key=credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=settings.audio_sas_hours),
    )
    return f"{blob.url}?{sas}"
