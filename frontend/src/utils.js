export function formatCompact(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(number);
}

export function formatMetric(value, digits = 2, suffix = "") {
  const number = Number(value || 0);
  return `${new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(number)}${suffix}`;
}

export function formatTimestamp(value) {
  if (!value) {
    return "Non disponible";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Non disponible";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

export function buildOperatorHighlights(journeys) {
  const buckets = new Map();

  journeys.forEach((journey) => {
    const key = journey.operator_name || "Operateur inconnu";
    const current = buckets.get(key) || { operator: key, count: 0, countries: new Set() };
    current.count += 1;
    if (journey.country_code) {
      current.countries.add(journey.country_code);
    }
    buckets.set(key, current);
  });

  return Array.from(buckets.values())
    .map((entry) => ({
      operator: entry.operator,
      count: entry.count,
      countries: Array.from(entry.countries).sort().join(", ")
    }))
    .sort((left, right) => right.count - left.count)
    .slice(0, 6);
}

export function buildVolumeHighlights(volumes) {
  return [...volumes]
    .sort((left, right) => right.total_trajets - left.total_trajets)
    .slice(0, 6);
}

export function serviceSplit(comparison) {
  const night = comparison.find((item) => item.train_type === "night");
  const day = comparison.find((item) => item.train_type === "day");
  const total = Number(night?.train_count || 0) + Number(day?.train_count || 0);

  if (!total) {
    return { nightShare: 0, dayShare: 0 };
  }

  return {
    nightShare: Math.round((Number(night?.train_count || 0) / total) * 100),
    dayShare: Math.round((Number(day?.train_count || 0) / total) * 100)
  };
}
