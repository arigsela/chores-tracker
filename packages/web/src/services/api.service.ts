import { apiClient } from './auth.service'
import { z } from 'zod'

// Base schemas
export const PaginationSchema = z.object({
  page: z.number().default(1),
  per_page: z.number().default(20),
  total: z.number(),
  total_pages: z.number(),
})

export const StandardResponseSchema = <T extends z.ZodType>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z.object({
      code: z.string(),
      message: z.string(),
      details: z.array(z.unknown()).optional(),
    }).optional(),
    metadata: z.object({
      timestamp: z.string(),
      version: z.string(),
      request_id: z.string(),
    }).optional(),
  })

// Error handling
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// Generic API methods
export const api = {
  async get<T>(url: string, schema: z.ZodType<T>) {
    try {
      const response = await apiClient.get(url)
      const standardResponse = response.data
      if (standardResponse.success && standardResponse.data) {
        return schema.parse(standardResponse.data)
      }
      throw new ApiError(
        standardResponse.error?.code || 'UNKNOWN_ERROR',
        standardResponse.error?.message || 'An error occurred',
        standardResponse.error?.details
      )
    } catch (error) {
      throw this.handleError(error)
    }
  },

  async post<T>(url: string, data: unknown, schema: z.ZodType<T>) {
    try {
      const response = await apiClient.post(url, data)
      const standardResponse = response.data
      if (standardResponse.success && standardResponse.data) {
        return schema.parse(standardResponse.data)
      }
      throw new ApiError(
        standardResponse.error?.code || 'UNKNOWN_ERROR',
        standardResponse.error?.message || 'An error occurred',
        standardResponse.error?.details
      )
    } catch (error) {
      throw this.handleError(error)
    }
  },

  async put<T>(url: string, data: unknown, schema: z.ZodType<T>) {
    try {
      const response = await apiClient.put(url, data)
      const standardResponse = response.data
      if (standardResponse.success && standardResponse.data) {
        return schema.parse(standardResponse.data)
      }
      throw new ApiError(
        standardResponse.error?.code || 'UNKNOWN_ERROR',
        standardResponse.error?.message || 'An error occurred',
        standardResponse.error?.details
      )
    } catch (error) {
      throw this.handleError(error)
    }
  },

  async delete(url: string) {
    try {
      const response = await apiClient.delete(url)
      const standardResponse = response.data
      if (!standardResponse.success) {
        throw new ApiError(
          standardResponse.error?.code || 'UNKNOWN_ERROR',
          standardResponse.error?.message || 'An error occurred',
          standardResponse.error?.details
        )
      }
    } catch (error) {
      throw this.handleError(error)
    }
  },

  handleError(error: unknown): ApiError {
    if (error instanceof ApiError) {
      return error
    }
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { data?: { error?: { code?: string; message?: string; details?: unknown } } } }
      const errorData = axiosError.response?.data?.error
      const { code, message, details } = errorData || {}
      return new ApiError(code || 'UNKNOWN_ERROR', message || 'An error occurred', details)
    }
    const message = error instanceof Error ? error.message : 'Network error occurred'
    return new ApiError('NETWORK_ERROR', message)
  },
}