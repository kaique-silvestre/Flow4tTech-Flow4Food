from src.models.assinaturas import Assinatura, AssinaturaHistory  # noqa: F401
from src.models.audit_logs import AuditLog  # noqa: F401
from src.models.auth import ConfigSeguranca  # noqa: F401
from src.models.billing import PagamentoAssinatura, Plano  # noqa: F401
from src.models.caixa import CaixaMovimento, CaixaSessao  # noqa: F401
from src.models.categorias import Categoria  # noqa: F401
from src.models.comandas import Comanda  # noqa: F401
from src.models.comissoes_garcom import ComissaoGarcom  # noqa: F401
from src.models.compras import Compra, ItemCompra  # noqa: F401
from src.models.consumo_interno import ItemConsumoInterno  # noqa: F401
from src.models.contas_pagar import ContaPagar, Notificacao  # noqa: F401
from src.models.eventos_comanda import EventoComanda  # noqa: F401
from src.models.ficha_tecnica import FichaTecnica  # noqa: F401
from src.models.fornecedores import Fornecedor  # noqa: F401
from src.models.garcons import Garcom  # noqa: F401
from src.models.insumos import Insumo  # noqa: F401
from src.models.itens_comanda import ItemComanda  # noqa: F401
from src.models.metodos_pagamento import MetodoPagamento  # noqa: F401
from src.models.movimentos_estoque import MovimentoEstoque  # noqa: F401
from src.models.pagamentos import Pagamento  # noqa: F401
from src.models.platform_admin import PlatformAdmin  # noqa: F401
from src.models.platform_announcements import (  # noqa: F401
    AnnouncementRead,
    AnnouncementTarget,
    PlatformAnnouncement,
)
from src.models.platform_settings import PlatformSettings  # noqa: F401
from src.models.produtos import Produto  # noqa: F401
from src.models.profiles import Profile, ProfilePermission  # noqa: F401
from src.models.refresh_tokens import RefreshToken  # noqa: F401
from src.models.revoked_tokens import RevokedToken  # noqa: F401
from src.models.system_users import PasswordReset, SystemUser  # noqa: F401
from src.models.tenant_features import TenantFeature  # noqa: F401
from src.models.tenants import Tenant  # noqa: F401
from src.models.user_permissions import UserPermission  # noqa: F401
