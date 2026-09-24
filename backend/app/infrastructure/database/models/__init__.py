"""Import all ORM models here so Alembic's autogenerate and
Base.metadata.create_all() can discover every mapped table."""
from app.infrastructure.database.models.asset_audit import AssetAuditModel  # noqa: F401
from app.infrastructure.database.models.asset_business import AssetBusinessModel  # noqa: F401
from app.infrastructure.database.models.asset_tag import AssetTagModel  # noqa: F401
from app.infrastructure.database.models.collector_run import CollectorRunModel  # noqa: F401
from app.infrastructure.database.models.inventory_asset import InventoryAssetModel  # noqa: F401
from app.infrastructure.database.models.inventory_network import InventoryNetworkModel  # noqa: F401
from app.infrastructure.database.models.inventory_storage import InventoryStorageModel  # noqa: F401
from app.infrastructure.database.models.site import SiteModel  # noqa: F401
from app.infrastructure.database.models.support_team import SupportTeamModel  # noqa: F401
from app.infrastructure.database.models.asset_attachment import AssetAttachmentModel  # noqa: F401
from app.infrastructure.database.models.system_setting import SystemSettingModel  # noqa: F401
from app.infrastructure.database.models.user import UserModel  # noqa: F401
