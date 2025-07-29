import { z } from 'zod'
import { api } from './api.service'
import { UserSchema } from './auth.service'

// Chore schemas
export const ChoreSchema = z.object({
  id: z.number(),
  title: z.string(),
  description: z.string(),
  reward_min: z.number(),
  reward_max: z.number().nullable(),
  status: z.enum(['created', 'pending', 'approved', 'disabled']),
  recurrence: z.enum(['once', 'daily', 'weekly', 'monthly']).nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  assignee: UserSchema.nullable(),
  created_by: UserSchema,
})

export const CreateChoreSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  reward_min: z.number().min(0, 'Minimum reward must be positive'),
  reward_max: z.number().min(0).nullable(),
  assignee_id: z.number(),
  recurrence: z.enum(['once', 'daily', 'weekly', 'monthly']).nullable(),
})

export type Chore = z.infer<typeof ChoreSchema>
export type CreateChoreData = z.infer<typeof CreateChoreSchema>

export const choreService = {
  async getChores() {
    return api.get('/api/v2/chores/', z.array(ChoreSchema))
  },

  async getChore(id: number) {
    return api.get(`/api/v2/chores/${id}`, ChoreSchema)
  },

  async createChore(data: CreateChoreData) {
    return api.post('/api/v2/chores/', data, ChoreSchema)
  },

  async updateChore(id: number, data: Partial<CreateChoreData>) {
    return api.put(`/api/v2/chores/${id}`, data, ChoreSchema)
  },

  async deleteChore(id: number) {
    return api.delete(`/api/v2/chores/${id}`)
  },

  async completeChore(id: number) {
    return api.post(`/api/v2/chores/${id}/complete`, {}, ChoreSchema)
  },

  async approveChore(id: number, rewardAmount: number) {
    return api.post(
      `/api/v2/chores/${id}/approve`,
      { reward_amount: rewardAmount },
      ChoreSchema
    )
  },

  async getAvailableChores() {
    return api.get('/api/v2/chores/available', z.array(ChoreSchema))
  },

  async getPendingApproval() {
    return api.get('/api/v2/chores/pending-approval', z.array(ChoreSchema))
  },
}