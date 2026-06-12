"""Seed a rich, repeatable local portfolio dataset for Locentr."""

import asyncio
import hashlib
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

load_dotenv(PROJECT_ROOT / ".env")

from src.core.enums import (
    AuditAction,
    InvitationStatus,
    SubscriptionStatus,
    SupportTicketStatus,
    TableName,
    UserRole,
)
from src.database import async_session, engine
from src.models import (
    AccessList,
    AccessLog,
    AuditLog,
    BillingInvoice,
    CommunicationPreference,
    Company,
    CompanyLocationAccess,
    CompanyStaff,
    CompanySubscription,
    Document,
    ExternalPeople,
    Location,
    LocationLogbook,
    LocationLogbookSettings,
    Notification,
    Plan,
    SupportResponse,
    SupportTicket,
    TenantInvitation,
    TypeAccessList,
    User,
    UserLocationAccess,
)

DEMO_EMAIL = os.getenv("LOCENTR_DEMO_EMAIL", "admin@nois.dev")
DEMO_USERNAME = os.getenv("LOCENTR_DEMO_USERNAME", "locentr-admin")
DEMO_FULL_NAME = os.getenv("LOCENTR_DEMO_FULL_NAME", "Boris Alvial")
DEMO_CREDENTIAL_HASH = os.getenv("LOCENTR_DEMO_CREDENTIAL_HASH")


def get_demo_credential_hash() -> str:
    """Return the demo credential hash from environment."""
    if not DEMO_CREDENTIAL_HASH:
        raise RuntimeError("LOCENTR_DEMO_CREDENTIAL_HASH is required.")
    return DEMO_CREDENTIAL_HASH


async def create_user(
    session: AsyncSession,
    *,
    username: str,
    full_name: str,
    email: str,
    role: UserRole,
    created_by: int | None,
) -> User:
    user = User(
        username=username,
        full_name=full_name,
        email=email,
        password_hash=get_demo_credential_hash(),
        role=role,
        status=True,
        is_active=True,
        email_verified_at=datetime.now(),
        created_by=created_by,
    )
    session.add(user)
    await session.flush()
    return user


async def seed_demo_data() -> None:
    """Create the complete local SaaS portfolio dataset."""
    now = datetime.now()
    async with async_session() as session:
        existing = await session.scalar(select(User.id).where(User.email == DEMO_EMAIL))
        if existing:
            print(f"Demo dataset already exists for {DEMO_EMAIL}")
            return

        root = await create_user(
            session,
            username=DEMO_USERNAME,
            full_name=DEMO_FULL_NAME,
            email=DEMO_EMAIL,
            role=UserRole.SUPERADMIN,
            created_by=None,
        )
        root.created_by = root.id

        company = Company(
            name="Viajes Cocha S.A.",
            activity="Agencia de viajes y gestión de servicios turísticos",
            id_number="77.418.620-3",
            type_document="RUT",
            created_by=root.id,
        )
        session.add(company)
        await session.flush()
        session.add_all(
            [
                Company(
                    name="Cocha Empresas",
                    activity="Viajes corporativos y gestión de cuentas empresa",
                    id_number="77.418.621-1",
                    type_document="RUT",
                    parent_company_id=company.id,
                    created_by=root.id,
                ),
                Company(
                    name="Cocha Eventos",
                    activity="Producción de eventos y viajes de incentivo",
                    id_number="77.418.622-K",
                    type_document="RUT",
                    parent_company_id=company.id,
                    created_by=root.id,
                ),
            ]
        )

        admin = await create_user(
            session,
            username="camila.admin",
            full_name="Camila Rojas",
            email="camila.rojas@cocha.com",
            role=UserRole.ADMIN,
            created_by=root.id,
        )
        operator_a = await create_user(
            session,
            username="matias.control",
            full_name="Matías Soto",
            email="matias.soto@cocha.com",
            role=UserRole.OPERATOR,
            created_by=root.id,
        )
        operator_b = await create_user(
            session,
            username="valentina.turno",
            full_name="Valentina Díaz",
            email="valentina.diaz@cocha.com",
            role=UserRole.OPERATOR,
            created_by=root.id,
        )
        client = await create_user(
            session,
            username="andres.cliente",
            full_name="Andrés Fuentes",
            email="andres.fuentes@cocha.com",
            role=UserRole.CLIENT,
            created_by=root.id,
        )
        users = [root, admin, operator_a, operator_b, client]
        session.add_all(
            [
                CompanyStaff(
                    company_id=company.id,
                    user_id=user.id,
                    created_by=root.id,
                )
                for user in users
            ]
        )

        locations = [
            Location(
                name="Casa Matriz Providencia",
                address="Av. Eliodoro Yáñez 2663, Providencia",
                country="Chile",
                created_by=root.id,
            ),
            Location(
                name="Sucursal Parque Arauco",
                address="Av. Presidente Kennedy 5413, Las Condes",
                country="Chile",
                created_by=root.id,
            ),
            Location(
                name="Centro Operativo Pudahuel",
                address="Av. Américo Vespucio 1309, Pudahuel",
                country="Chile",
                created_by=root.id,
            ),
        ]
        session.add_all(locations)
        await session.flush()
        session.add_all(
            [
                CompanyLocationAccess(
                    company_id=company.id,
                    location_id=location.id,
                    created_by=root.id,
                )
                for location in locations
            ]
        )
        session.add_all(
            [
                UserLocationAccess(
                    user_id=user.id,
                    location_id=location.id,
                    created_by=root.id,
                )
                for user in users
                for location in locations
            ]
        )

        growth = await session.scalar(select(Plan).where(Plan.code == "growth"))
        if not growth:
            raise RuntimeError("Growth plan was not created by migrations.")
        session.add(
            CompanySubscription(
                company_id=company.id,
                plan_id=growth.id,
                status=SubscriptionStatus.ACTIVE,
                trial_started_at=now - timedelta(days=38),
                trial_ends_at=now - timedelta(days=24),
                current_period_start=now - timedelta(days=8),
                current_period_end=now + timedelta(days=22),
                provider_customer_id="cus_demo_locentr",
                provider_subscription_id="sub_demo_locentr",
            )
        )
        session.add(
            CommunicationPreference(
                company_id=company.id,
                billing_emails=True,
                product_emails=True,
                updated_by=root.id,
            )
        )
        session.add_all(
            [
                BillingInvoice(
                    company_id=company.id,
                    provider_invoice_id=f"in_demo_{month}",
                    status="paid",
                    currency="usd",
                    amount_due=7900,
                    amount_paid=7900,
                    hosted_invoice_url=("https://dashboard.stripe.com/test/invoices"),
                    period_start=now - timedelta(days=30 * month),
                    period_end=now - timedelta(days=30 * (month - 1)),
                    created_at=now - timedelta(days=30 * month),
                    updated_at=now - timedelta(days=30 * month),
                )
                for month in range(1, 4)
            ]
        )

        access_types = [
            TypeAccessList(name="whitelist", created_by=root.id),
            TypeAccessList(name="blacklist", created_by=root.id),
        ]
        session.add_all(access_types)
        await session.flush()
        people = [
            ExternalPeople(
                name=name,
                id_number=id_number,
                created_by=admin.id,
                created_at=now - timedelta(days=index + 1),
            )
            for index, (name, id_number) in enumerate(
                [
                    ("Sofía Martínez", "18.445.221-7"),
                    ("Diego Herrera", "16.904.883-2"),
                    ("Paula Contreras", "19.223.761-5"),
                    ("Sebastián Vega", "17.681.429-0"),
                    ("Daniela Silva", "20.118.944-3"),
                    ("Tomás Morales", "15.762.031-8"),
                    ("Fernanda Lagos", "18.991.604-K"),
                    ("Nicolás Paredes", "17.408.112-1"),
                ]
            )
        ]
        session.add_all(people)
        await session.flush()
        session.add_all(
            [
                AccessList(
                    company_id=company.id,
                    location_id=locations[index % len(locations)].id,
                    external_people_id=person.id,
                    type_access_list_id=access_types[index % 2].id,
                    name=person.name,
                    reason=(
                        "Reunión con equipo comercial"
                        if index % 2 == 0
                        else "Mantención programada"
                    ),
                    vehicle_plate=f"LC{index + 20}TR",
                    expiration_date=now + timedelta(days=7 + index),
                    created_by=admin.id,
                    created_at=now - timedelta(days=index),
                )
                for index, person in enumerate(people[:6])
            ]
        )
        session.add_all(
            [
                AccessLog(
                    location_id=locations[index % len(locations)].id,
                    external_people_id=people[index % len(people)].id,
                    type_document="RUT",
                    vehicle_plate=f"LC{index + 30}NT",
                    office=f"{10 + index}0{index % 5 + 1}",
                    comment=(
                        "Reunión agendada" if index % 3 else "Proveedor acreditado"
                    ),
                    exit_date=(
                        now - timedelta(hours=index % 7) if index % 4 != 0 else None
                    ),
                    exit_comment=("Salida registrada" if index % 4 != 0 else None),
                    exit_created_by=(operator_a.id if index % 4 != 0 else None),
                    created_by=(operator_a.id if index % 2 == 0 else operator_b.id),
                    created_at=(
                        now - timedelta(hours=index * 2, minutes=index * 3)
                        if index < 8
                        else now - timedelta(days=(index - 7) * 12, hours=index)
                    ),
                )
                for index in range(24)
            ]
        )

        session.add_all(
            [
                Document(
                    name=name,
                    file_name=file_name,
                    blob_name=f"companies/{company.id}/{file_name}",
                    company_id=company.id,
                    user_id=admin.id,
                    comment=comment,
                    content_type=content_type,
                    size_bytes=size_bytes,
                    created_by=admin.id,
                    created_at=now - timedelta(days=days),
                )
                for name, file_name, comment, content_type, size_bytes, days in [
                    (
                        "Protocolo de evacuación",
                        "protocolo-evacuacion-2026.pdf",
                        "Versión aprobada para todas las sedes",
                        "application/pdf",
                        2_480_000,
                        5,
                    ),
                    (
                        "Matriz de riesgos",
                        "matriz-riesgos-q2.xlsx",
                        "Evaluación trimestral",
                        (
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        1_160_000,
                        12,
                    ),
                    (
                        "Manual de proveedores",
                        "manual-proveedores.pdf",
                        "Lineamientos de acreditación",
                        "application/pdf",
                        980_000,
                        18,
                    ),
                ]
            ]
        )

        tickets = [
            SupportTicket(
                title="Integración lector acceso norte",
                description=(
                    "Validar el nuevo lector QR instalado en la entrada norte."
                ),
                status=SupportTicketStatus.IN_PROGRESS,
                created_by=admin.id,
                created_at=now - timedelta(days=2),
            ),
            SupportTicket(
                title="Reporte mensual de accesos",
                description=("Agregar el detalle de visitas agrupadas por empresa."),
                status=SupportTicketStatus.OPEN,
                created_by=admin.id,
                created_at=now - timedelta(days=1),
            ),
            SupportTicket(
                title="Actualización de permisos",
                description="La matriz de permisos quedó revisada y operativa.",
                status=SupportTicketStatus.RESOLVED,
                created_by=admin.id,
                created_at=now - timedelta(days=8),
            ),
        ]
        session.add_all(tickets)
        await session.flush()
        session.add(
            SupportResponse(
                ticket_id=tickets[0].id,
                comment=(
                    "Configuración recibida. Estamos revisando los eventos "
                    "del dispositivo."
                ),
                created_by=root.id,
                created_at=now - timedelta(days=1),
            )
        )

        session.add_all(
            [
                LocationLogbookSettings(
                    location_id=location.id,
                    is_enabled=True,
                    updated_by=admin.id,
                    updated_at=now,
                )
                for location in locations
            ]
        )
        session.add_all(
            [
                LocationLogbook(
                    location_id=locations[index % len(locations)].id,
                    created_by=(operator_a.id if index % 2 == 0 else operator_b.id),
                    description=description,
                    created_at=now - timedelta(hours=index * 7),
                )
                for index, description in enumerate(
                    [
                        "Turno recibido sin novedades críticas.",
                        "Mantención preventiva de ascensores coordinada.",
                        "Climatización del piso 14 revisada.",
                        "Simulacro de evacuación completado en 7 minutos.",
                        "Acceso de estacionamiento normalizado.",
                        "Credenciales temporales entregadas a eventos.",
                    ]
                )
            ]
        )

        session.add_all(
            [
                Notification(
                    title="Operación saludable",
                    message="Las tres sedes reportan actividad normal.",
                    created_by_user_id=root.id,
                    user_id=admin.id,
                    created_at=now - timedelta(minutes=18),
                ),
                Notification(
                    title="Factura disponible",
                    message="La factura del período actual fue confirmada.",
                    created_by_user_id=root.id,
                    user_id=admin.id,
                    created_at=now - timedelta(days=1),
                ),
                Notification(
                    title="Nueva respuesta de soporte",
                    message="El ticket del lector QR recibió una actualización.",
                    created_by_user_id=root.id,
                    user_id=admin.id,
                    created_at=now - timedelta(days=1, hours=4),
                ),
            ]
        )
        session.add_all(
            [
                AuditLog(
                    user_id=root.id,
                    action=action,
                    table_name=TableName.USERS,
                    record_id=index + 1,
                    description=description,
                    created_at=now - timedelta(hours=index * 5),
                )
                for index, (action, description) in enumerate(
                    [
                        (AuditAction.CREATE, "Empresa Viajes Cocha creada."),
                        (
                            AuditAction.ACCESS_GRANTED,
                            "Acceso de Camila Rojas habilitado.",
                        ),
                        (
                            AuditAction.UPDATE,
                            "Plan Growth sincronizado correctamente.",
                        ),
                        (
                            AuditAction.LOGIN,
                            "Inicio de sesión administrativo exitoso.",
                        ),
                        (
                            AuditAction.UPDATE,
                            "Permisos de sedes actualizados.",
                        ),
                    ]
                )
            ]
        )

        invitation_token = "demo-invitation-operator"
        session.add(
            TenantInvitation(
                company_id=company.id,
                invited_by=admin.id,
                email="francisca.nunez@cocha.com",
                full_name="Francisca Núñez",
                username="francisca.turno",
                role=UserRole.OPERATOR,
                token_hash=hashlib.sha256(invitation_token.encode()).hexdigest(),
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(days=3),
            )
        )

        await session.commit()
        print(
            "Created rich demo dataset: "
            f"{company.name}, {len(locations)} locations, "
            f"{len(users)} users, 24 access logs"
        )


async def main() -> None:
    """Run the demo seed and dispose database resources."""
    try:
        await seed_demo_data()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
