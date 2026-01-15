import request from '@/utils/request'

const api = {
    agentStart: '/api/indicator/backtest/agent/start',
    agentControl: '/api/indicator/backtest/agent/control',
    agentStatus: '/api/indicator/backtest/agent/status'
}

/**
 * Start Auto-Optimization Agent
 * @param {Object} data
 * @param {Object} data.config - Initial Backtest Params
 * @param {string} data.strategy_code - Strategy Code
 * @param {string} data.target_metric - 'sharpeRatio' | 'totalReturn' | 'winRate'
 * @param {number} data.max_iterations - Max loops
 */
export function startAgentOptimization (data) {
    return request({
        url: api.agentStart,
        method: 'post',
        data
    })
}

/**
 * Control Agent Job
 * @param {string} jobId
 * @param {string} action - 'pause' | 'resume' | 'stop'
 */
export function controlAgentJob (jobId, action) {
    return request({
        url: api.agentControl,
        method: 'post',
        data: {
            job_id: jobId,
            action
        }
    })
}

/**
 * Get Agent Job Status
 * @param {string} jobId
 */
export function getAgentJobStatus (jobId) {
    return request({
        url: `${api.agentStatus}/${jobId}`,
        method: 'get'
    })
}
