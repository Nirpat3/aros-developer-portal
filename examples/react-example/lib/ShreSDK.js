/**
 * Browser-compatible Shre SDK
 * Sends events to apiauth.shre.ai/v1/events/batch
 */
export class ShreSDK {
  constructor(tenantId, baseUrl = 'https://apiauth.shre.ai') {
    this.tenantId = tenantId
    this.baseUrl = baseUrl.replace(/\/$/, '')
    this.authToken = null
    this.sessionExpiry = null
  }

  async sendEventsBatch(events) {
    const url = `${this.baseUrl}/v1/events/batch`
    const headers = {
      'Content-Type': 'application/json',
      'x-shre-tenant': this.tenantId,
      'x-shre-app': 'web',
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ events }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`)
      }

      return await response.json()
    } catch (error) {
      throw new Error(`Failed to send events: ${error.message}`)
    }
  }

  async createSession(bootstrapKey) {
    const url = `${this.baseUrl}/v1/sdk/session`
    const headers = {
      'Content-Type': 'application/json',
      'x-shre-tenant': this.tenantId,
      'x-shre-app': bootstrapKey,
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({}),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      this.authToken = data.access_token
      this.sessionExpiry = new Date(Date.now() + data.expires_in * 1000)
      return data
    } catch (error) {
      throw new Error(`Session creation failed: ${error.message}`)
    }
  }

  async getConfig() {
    const url = `${this.baseUrl}/v1/sdk/config`
    const headers = {
      'x-shre-tenant': this.tenantId,
    }

    try {
      const response = await fetch(url, { method: 'GET', headers })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      throw new Error(`Config fetch failed: ${error.message}`)
    }
  }

  async sendHeartbeat(deviceId, eventsQueued, eventsSent = 0) {
    const url = `${this.baseUrl}/v1/sdk/heartbeat`
    const headers = {
      'Content-Type': 'application/json',
      'x-shre-tenant': this.tenantId,
      'x-shre-app': 'web',
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          tenantId: this.tenantId,
          app: 'web',
          deviceId,
          eventsQueued,
          eventsSent,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      throw new Error(`Heartbeat failed: ${error.message}`)
    }
  }
}
