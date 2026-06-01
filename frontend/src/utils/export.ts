export function downloadFile(content: string, filename: string, mime: string) {
  const blob = new Blob(['\uFEFF' + content], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function escapeCSV(value: unknown): string {
  const str = String(value ?? '')
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export function exportToCSV<T extends Record<string, unknown>>(
  data: T[],
  filename: string,
  columns?: { key: keyof T; title: string }[]
) {
  if (data.length === 0) return

  const keys = columns
    ? columns.map((c) => c.key)
    : (Object.keys(data[0]) as (keyof T)[])

  const headerRow = columns
    ? columns.map((c) => escapeCSV(c.title)).join(',')
    : keys.map((k) => escapeCSV(String(k))).join(',')

  const rows = data.map((row) =>
    keys.map((k) => escapeCSV(row[k])).join(',')
  )

  const csv = [headerRow, ...rows].join('\n')
  downloadFile(csv, filename, 'text/csv;charset=utf-8')
}

export function exportToJSON<T>(data: T[], filename: string) {
  const json = JSON.stringify(data, null, 2)
  downloadFile(json, filename, 'application/json')
}
