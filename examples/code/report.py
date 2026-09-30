"""Ejemplo ficticio: reporte JSON de etiquetas activas; no es código de producción."""


def build_report(records):
    if not isinstance(records, list):
        raise ValueError('records must be a list')
    for row in records:
        if not isinstance(row, dict) or set(row) != {'name', 'active'}:
            raise ValueError('each record must contain name and active only')
        if not isinstance(row['name'], str) or not row['name'].strip() or type(row['active']) is not bool:
            raise ValueError('name must be non-empty and active must be boolean')
    names = sorted(row['name'] for row in records if row['active'])
    return {'active_count': len(names), 'names': names}
