import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
  type ColumnDef as TanStackColumnDef,
} from "@tanstack/react-table"
import { useState, useMemo, type ReactNode } from "react"
import { cn } from "../../lib/utils"

interface ColumnDef {
  header: string
  accessorKey: string
  cell?: (value: unknown) => ReactNode
}

interface Props {
  columns: ColumnDef[]
  data: Record<string, unknown>[]
  className?: string
}

export default function DataTable({ columns, data, className }: Props) {
  const [sorting, setSorting] = useState<SortingState>([])

  const tableColumns = useMemo<TanStackColumnDef<Record<string, unknown>>[]>(
    () =>
      columns.map((col) => ({
        accessorKey: col.accessorKey,
        header: col.header,
        cell: (info) => {
          const val = info.getValue()
          return col.cell ? col.cell(val) : String(val)
        },
      })),
    [columns]
  )

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div
      className={cn(
        "rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] shadow-[var(--shadow-border)] overflow-hidden",
        className
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b" style={{ borderColor: "var(--clr-gray-20)" }}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer select-none"
                    style={{ color: "var(--clr-text-secondary)" }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: " ↑", desc: " ↓" }[header.column.getIsSorted() as string] ?? ""}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b last:border-0 transition-colors"
                style={{ borderColor: "var(--clr-gray-20)" }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--clr-surface-hover)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "")}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3" style={{ color: "var(--clr-text-primary)" }}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
