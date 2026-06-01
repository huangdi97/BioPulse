import client from './client'
import type { Task } from '@/types'
import { mockTasks } from '@/mock/tasks'

export async function fetchTasks(status?: string): Promise<Task[]> {
  try {
    const response = await client.get<Task[]>('/api/assistant/tasks', {
      params: status ? { status } : undefined,
    })
    return response.data
  } catch {
    if (status) {
      return mockTasks.filter((t) => t.status === status)
    }
    return mockTasks
  }
}

export async function completeTask(id: number): Promise<Task | null> {
  try {
    const response = await client.patch<Task>(`/api/assistant/tasks/${id}`, {
      status: 'completed',
    })
    return response.data
  } catch {
    const task = mockTasks.find((t) => t.id === id)
    if (task) {
      task.status = 'completed'
    }
    return task ?? null
  }
}
