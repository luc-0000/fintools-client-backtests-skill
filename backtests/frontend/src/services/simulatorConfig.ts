import { get, put } from '@/utils/request'

export const simulatorConfigService = {
  getConfig: () => {
    return get('/v1/get_simulator/config')
  },

  updateConfig: (data: any) => {
    return put('/v1/get_simulator/config', data)
  },
}
