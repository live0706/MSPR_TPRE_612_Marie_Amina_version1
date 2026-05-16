def build_trajet_params(country_code=None, operator_name=None, year=None, service_type=None, search=None, limit=200):
    params = {"limit": limit}
    if country_code and country_code != "Tous":
        params["country_code"] = country_code
    if operator_name and operator_name != "Tous":
        params["operator_name"] = operator_name
    if year and year != "Tous":
        params["year"] = int(year)
    if service_type and service_type != "Tous":
        params["service_type"] = service_type
    if search:
        params["search"] = search.strip()
    return params


def normalize_status_label(status):
    value = (status or "").strip().lower()
    if value == "ok":
        return "Operationnel"
    if value == "degraded":
        return "Degrade"
    if value == "error":
        return "Critique"
    return "Inconnu"
