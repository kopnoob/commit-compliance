"""
Commit AS — Internal billing calculator
No personal data in this module.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProjectBilling:
    project_id: str
    hours: Decimal
    rate_nok: Decimal
    
    @property
    def total(self) -> Decimal:
        return self.hours * self.rate_nok
    
    def invoice_line(self) -> str:
        return f"Prosjekt {self.project_id}: {self.hours}t × {self.rate_nok} NOK = {self.total} NOK"


def calculate_monthly_billing(projects: list[ProjectBilling]) -> Decimal:
    """Calculate total monthly billing across all projects."""
    return sum(p.total for p in projects)


# Example usage
if __name__ == "__main__":
    projects = [
        ProjectBilling("ACME-2024", Decimal("160"), Decimal("1450")),
        ProjectBilling("BETA-2024", Decimal("80"), Decimal("1600")),
    ]
    total = calculate_monthly_billing(projects)
    print(f"Total fakturering: {total} NOK")
