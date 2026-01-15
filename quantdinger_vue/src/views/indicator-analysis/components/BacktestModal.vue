<template>
  <a-modal
    :title="$t('dashboard.indicator.backtest.title')"
    :visible="visible"
    :width="1100"
    @cancel="handleCancel"
    :maskClosable="false"
    class="backtest-modal"
  >
    <div class="backtest-content">
      <a-tabs v-model="activeTab">
        <a-tab-pane key="manual" :tab="$t('dashboard.indicator.backtest.tabManual') || 'Manual Backtest'">
          <a-steps :current="currentStep" size="small" style="margin-bottom: 16px;">
            <a-step :title="$t('dashboard.indicator.backtest.steps.strategy.title')" :description="$t('dashboard.indicator.backtest.steps.strategy.desc')" />
            <a-step :title="$t('dashboard.indicator.backtest.steps.trading.title')" :description="$t('dashboard.indicator.backtest.steps.trading.desc')" />
            <a-step :title="$t('dashboard.indicator.backtest.steps.results.title')" :description="$t('dashboard.indicator.backtest.steps.results.desc')" />
          </a-steps>

          <!-- Steps 1 & 2: configuration -->
          <div v-show="currentStep !== 2" class="config-section">
            <a-form :form="form" :label-col="labelCol" :wrapper-col="wrapperCol">
              <!-- Step 1: strategy settings -->
              <div v-show="currentStep === 0">
                <a-collapse v-model="step1CollapseKeys" :bordered="false" style="background: #fafafa;">
                  <a-collapse-panel key="risk" :header="$t('dashboard.indicator.backtest.panel.risk')">
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.stopLossPct')">
                          <a-input-number
                            v-decorator="['stopLossPct', { initialValue: 0 }]"
                            :min="0"
                            :max="100"
                            :step="0.01"
                            :precision="4"
                            style="width: 220px"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.takeProfitPct')">
                          <a-input-number
                            v-decorator="['takeProfitPct', { initialValue: 0 }]"
                            :min="0"
                            :max="1000"
                            :step="0.01"
                            :precision="4"
                            style="width: 220px"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>

                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trailingEnabled')">
                          <a-switch
                            v-decorator="['trailingEnabled', { valuePropName: 'checked', initialValue: false }]"
                            @change="onTrailingToggle"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12"></a-col>
                    </a-row>

                    <template v-if="trailingEnabledUi">
                      <a-row :gutter="24">
                        <a-col :span="12">
                          <a-form-item :label="$t('dashboard.indicator.backtest.field.trailingStopPct')">
                            <a-input-number
                              v-decorator="['trailingStopPct', { initialValue: 0 }]"
                              :min="0"
                              :max="100"
                              :step="0.01"
                              :precision="4"
                              style="width: 220px"
                            />
                          </a-form-item>
                        </a-col>
                        <a-col :span="12">
                          <a-form-item :label="$t('dashboard.indicator.backtest.field.trailingActivationPct')">
                            <a-input-number
                              v-decorator="['trailingActivationPct', { initialValue: 0 }]"
                              :min="0"
                              :max="1000"
                              :step="0.01"
                              :precision="4"
                              style="width: 220px"
                            />
                          </a-form-item>
                        </a-col>
                      </a-row>
                    </template>
                  </a-collapse-panel>

                  <a-collapse-panel key="scale" :header="$t('dashboard.indicator.backtest.panel.scale')">
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendAddEnabled')">
                          <a-switch
                            v-decorator="['trendAddEnabled', { valuePropName: 'checked', initialValue: false }]"
                            @change="onTrendAddToggle"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.dcaAddEnabled')">
                          <a-switch
                            v-decorator="['dcaAddEnabled', { valuePropName: 'checked', initialValue: false }]"
                            @change="onDcaAddToggle"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendAddStepPct')">
                          <a-input-number
                            v-decorator="['trendAddStepPct', { initialValue: 0 }]"
                            :min="0"
                            :max="1000"
                            :step="0.01"
                            :precision="4"
                            style="width: 220px"
                            @change="onScaleParamsChange"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.dcaAddStepPct')">
                          <a-input-number
                            v-decorator="['dcaAddStepPct', { initialValue: 0 }]"
                            :min="0"
                            :max="1000"
                            :step="0.01"
                            :precision="4"
                            style="width: 220px"
                            @change="onScaleParamsChange"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendAddSizePct')">
                          <a-input-number
                            v-decorator="['trendAddSizePct', { initialValue: 0 }]"
                            :min="0"
                            :max="100"
                            :step="0.1"
                            :precision="4"
                            style="width: 220px"
                            @change="onScaleParamsChange"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.dcaAddSizePct')">
                          <a-input-number
                            v-decorator="['dcaAddSizePct', { initialValue: 0 }]"
                            :min="0"
                            :max="100"
                            :step="0.1"
                            :precision="4"
                            style="width: 220px"
                            @change="onScaleParamsChange"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendAddMaxTimes')">
                          <a-input-number
                            v-decorator="['trendAddMaxTimes', { initialValue: 0 }]"
                            :min="0"
                            :max="50"
                            :step="1"
                            :precision="0"
                            style="width: 220px"
                            @change="onScaleParamsChange"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.dcaAddMaxTimes')">
                          <a-input-number
                            v-decorator="['dcaAddMaxTimes', { initialValue: 0 }]"
                            :min="0"
                            :max="50"
                            :step="1"
                            :precision="0"
                            style="width: 220px"
                            @change="onScaleParamsChange"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                  </a-collapse-panel>

                  <a-collapse-panel key="reduce" :header="$t('dashboard.indicator.backtest.panel.reduce')">
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendReduceEnabled')">
                          <a-switch v-decorator="['trendReduceEnabled', { valuePropName: 'checked', initialValue: false }]" />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.adverseReduceEnabled')">
                          <a-switch v-decorator="['adverseReduceEnabled', { valuePropName: 'checked', initialValue: false }]" />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendReduceStepPct')">
                          <a-input-number
                            v-decorator="['trendReduceStepPct', { initialValue: 0 }]"
                            :min="0"
                            :max="1000"
                            :step="0.01"
                            :precision="4"
                            style="width: 220px"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.adverseReduceStepPct')">
                          <a-input-number
                            v-decorator="['adverseReduceStepPct', { initialValue: 0 }]"
                            :min="0"
                            :max="1000"
                            :step="0.01"
                            :precision="4"
                            style="width: 220px"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendReduceSizePct')">
                          <a-input-number
                            v-decorator="['trendReduceSizePct', { initialValue: 0 }]"
                            :min="0"
                            :max="100"
                            :step="0.1"
                            :precision="4"
                            style="width: 220px"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.adverseReduceSizePct')">
                          <a-input-number
                            v-decorator="['adverseReduceSizePct', { initialValue: 0 }]"
                            :min="0"
                            :max="100"
                            :step="0.1"
                            :precision="4"
                            style="width: 220px"
                          />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.trendReduceMaxTimes')">
                          <a-input-number
                            v-decorator="['trendReduceMaxTimes', { initialValue: 0 }]"
                            :min="0"
                            :max="50"
                            :step="1"
                            :precision="0"
                            style="width: 100%" />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.adverseReduceMaxTimes')">
                          <a-input-number
                            v-decorator="['adverseReduceMaxTimes', { initialValue: 0 }]"
                            :min="0"
                            :max="50"
                            :step="1"
                            :precision="0"
                            style="width: 100%" />
                        </a-form-item>
                      </a-col>
                    </a-row>
                  </a-collapse-panel>

                  <a-collapse-panel key="position" :header="$t('dashboard.indicator.backtest.panel.position')">
                    <a-row :gutter="24">
                      <a-col :span="12">
                        <a-form-item :label="$t('dashboard.indicator.backtest.field.entryPct')" :help="$t('dashboard.indicator.backtest.hint.entryPctMax', { maxPct: Number(entryPctMaxUi || 0).toFixed(0) })">
                          <a-input-number
                            v-decorator="['entryPct', { initialValue: 100 }]"
                            :min="0"
                            :max="entryPctMaxUi"
                            :step="0.1"
                            :precision="4"
                            style="width: 220px"
                            @change="onEntryPctChange"
                          />
                        </a-form-item>
                      </a-col>
                      <a-col :span="12"></a-col>
                    </a-row>
                  </a-collapse-panel>
                </a-collapse>
              </div>

              <!-- Step 2: trading settings -->
              <div v-show="currentStep === 1">
                <!-- 合并的信息提示：交易对信息 + 精度信息 -->
                <a-alert
                  :type="combinedAlertType"
                  show-icon
                  style="margin-bottom: 12px;"
                >
                  <template slot="message">
                    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px;">
                      <!-- 基本信息 -->
                      <span>
                        <strong>Symbol:</strong> {{ symbol || '-' }}
                        <span style="color: #999; margin: 0 6px;">|</span>
                        <strong>Market:</strong> {{ market || '-' }}
                        <span style="color: #999; margin: 0 6px;">|</span>
                        <strong>Timeframe:</strong> {{ selectedTimeframe || timeframe || '-' }}
                      </span>
                      <!-- 精度信息 -->
                      <span v-if="precisionInfo && precisionInfo.enabled" style="margin-left: 12px; border-left: 1px solid #d9d9d9; padding-left: 12px;">
                        <a-icon :type="precisionInfo.precision === 'high' ? 'thunderbolt' : 'clock-circle'" style="margin-right: 4px;" />
                        {{ $t('dashboard.indicator.backtest.precisionMode') }}:
                        <a-tag :color="precisionInfo.precision === 'high' ? 'green' : 'blue'" size="small" style="margin-left: 4px;">
                          {{ precisionInfo.timeframe }}
                        </a-tag>
                        <span style="color: #666; margin-left: 6px;">
                          ({{ $t('dashboard.indicator.backtest.estimatedCandles', { count: precisionInfo.estimated_candles ? precisionInfo.estimated_candles.toLocaleString() : '-' }) }})
                        </span>
                      </span>
                      <span v-else-if="precisionInfo && !precisionInfo.enabled && market && market.toLowerCase() === 'crypto'" style="margin-left: 12px; border-left: 1px solid #d9d9d9; padding-left: 12px; color: #faad14;">
                        <a-icon type="warning" style="margin-right: 4px;" />
                        {{ $t('dashboard.indicator.backtest.standardModeWarning') }}
                      </span>
                    </div>
                  </template>
                  <template slot="description">
                    <span v-if="precisionInfo && precisionInfo.enabled" style="font-size: 12px; color: #888;">
                      {{ precisionInfo.precision === 'high' ? $t('dashboard.indicator.backtest.highPrecisionDesc') : $t('dashboard.indicator.backtest.mediumPrecisionDesc') }}
                    </span>
                    <span v-else-if="precisionInfo && !precisionInfo.enabled && market && market.toLowerCase() === 'crypto'" style="font-size: 12px; color: #888;">
                      {{ precisionInfo.message || $t('dashboard.indicator.backtest.standardModeDesc') }}
                    </span>
                  </template>
                </a-alert>

                <!-- 快捷日期选择按钮 -->
                <div class="date-quick-select" style="margin-bottom: 12px;">
                  <span style="margin-right: 8px; color: #666; font-size: 13px;">{{ $t('dashboard.indicator.backtest.quickSelect') || '快速选择' }}:</span>
                  <a-button-group size="small">
                    <a-button
                      v-for="preset in datePresets"
                      :key="preset.key"
                      :type="selectedDatePreset === preset.key ? 'primary' : 'default'"
                      @click="applyDatePreset(preset)"
                    >{{ preset.label }}</a-button>
                  </a-button-group>
                </div>

                <a-row :gutter="24">
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.startDate')">
                      <a-date-picker
                        v-decorator="['startDate', { rules: [{ required: true, message: $t('dashboard.indicator.backtest.startDateRequired') }], initialValue: defaultStartDate }]"
                        style="width: 100%"
                        :disabled-date="disabledStartDate"
                        :placeholder="$t('dashboard.indicator.backtest.selectStartDate')"
                        @change="onDateChange"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.endDate')">
                      <a-date-picker
                        v-decorator="['endDate', { rules: [{ required: true, message: $t('dashboard.indicator.backtest.endDateRequired') }], initialValue: defaultEndDate }]"
                        style="width: 100%"
                        :disabled-date="disabledEndDate"
                        :placeholder="$t('dashboard.indicator.backtest.selectEndDate')"
                        @change="onDateChange"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-row :gutter="24">
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.initialCapital')">
                      <a-input-number
                        v-decorator="['initialCapital', { rules: [{ required: true, message: $t('dashboard.indicator.backtest.initialCapitalRequired') }], initialValue: 10000 }]"
                        :min="1000"
                        :step="10000"
                        :precision="2"
                        style="width: 100%"
                        :formatter="value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')"
                        :parser="value => value.replace(/\$\s?|(,*)/g, '')"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.commission')">
                      <a-input-number
                        v-decorator="['commission', { initialValue: 0.02 }]"
                        :min="0"
                        :max="10"
                        :step="0.01"
                        :precision="4"
                        style="width: 100%"
                      />
                      <div class="field-hint">{{ $t('dashboard.indicator.backtest.commissionHint') }}</div>
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-row :gutter="24">
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.field.slippage')">
                      <a-input-number
                        v-decorator="['slippage', { initialValue: 0 }]"
                        :min="0"
                        :max="10"
                        :step="0.01"
                        :precision="4"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.leverage')">
                      <a-input-number
                        v-decorator="['leverage', { initialValue: 1 }]"
                        :min="1"
                        :max="125"
                        :step="1"
                        :precision="0"
                        style="width: 100%"
                        :formatter="value => `${value}x`"
                        :parser="value => value.replace('x', '')"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-row :gutter="24">
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.tradeDirection')">
                      <a-select
                        v-decorator="['tradeDirection', { initialValue: 'long' }]"
                        style="width: 100%"
                      >
                        <a-select-option value="long">
                          {{ $t('dashboard.indicator.backtest.longOnly') }}
                        </a-select-option>
                        <a-select-option value="short">
                          {{ $t('dashboard.indicator.backtest.shortOnly') }}
                        </a-select-option>
                        <a-select-option value="both">
                          {{ $t('dashboard.indicator.backtest.both') }}
                        </a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item :label="$t('dashboard.indicator.backtest.timeframe')">
                      <a-select
                        v-model="selectedTimeframe"
                        style="width: 100%"
                        @change="onTimeframeChange"
                      >
                        <a-select-option value="1m">1m</a-select-option>
                        <a-select-option value="5m">5m</a-select-option>
                        <a-select-option value="15m">15m</a-select-option>
                        <a-select-option value="30m">30m</a-select-option>
                        <a-select-option value="1H">1H</a-select-option>
                        <a-select-option value="4H">4H</a-select-option>
                        <a-select-option value="1D">1D</a-select-option>
                        <a-select-option value="1W">1W</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>
              </div>
            </a-form>
          </div>

          <!-- 回测结果区域 -->
          <div v-show="currentStep === 2 && hasResult" class="result-section">
            <a-alert
              v-if="backtestRunId"
              type="success"
              show-icon
              style="margin-bottom: 12px;"
              :message="$t('dashboard.indicator.backtest.savedRunId', { id: backtestRunId })"
            />

            <!-- 关键指标卡片 -->
            <div class="metrics-cards">
              <div class="metric-card" :class="{ positive: result.totalReturn > 0, negative: result.totalReturn < 0 }">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.totalReturn') }}</div>
                <div class="metric-value">{{ formatPercent(result.totalReturn) }}</div>
                <div class="metric-amount">{{ formatMoney(result.totalProfit) }}</div>
              </div>
              <div class="metric-card" :class="{ positive: result.annualReturn > 0, negative: result.annualReturn < 0 }">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.annualReturn') }}</div>
                <div class="metric-value">{{ formatPercent(result.annualReturn) }}</div>
              </div>
              <div class="metric-card negative">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.maxDrawdown') }}</div>
                <div class="metric-value">{{ formatPercent(result.maxDrawdown) }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.sharpeRatio') }}</div>
                <div class="metric-value">{{ result.sharpeRatio.toFixed(2) }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.winRate') }}</div>
                <div class="metric-value">{{ formatPercent(result.winRate) }}</div>
              </div>
              <div class="metric-card" :class="{ positive: result.profitFactor >= 1.5, negative: result.profitFactor < 1 }">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.profitFactor') }}</div>
                <div class="metric-value">{{ result.profitFactor.toFixed(2) }}</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.totalTrades') }}</div>
                <div class="metric-value">{{ result.totalTrades }}</div>
              </div>
              <div class="metric-card negative">
                <div class="metric-label">{{ $t('dashboard.indicator.backtest.totalCommission') }}</div>
                <div class="metric-value">-${{ result.totalCommission ? result.totalCommission.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00' }}</div>
              </div>
            </div>

            <!-- 收益曲线图表 -->
            <div class="chart-section">
              <div class="chart-title">{{ $t('dashboard.indicator.backtest.equityCurve') }}</div>
              <div ref="equityChartRef" class="equity-chart"></div>
            </div>

            <!-- 交易记录表格 -->
            <div class="trades-section">
              <div class="chart-title">{{ $t('dashboard.indicator.backtest.tradeHistory') }}</div>
              <a-table
                :columns="tradeColumns"
                :data-source="result.trades"
                :pagination="{ pageSize: 5, size: 'small' }"
                size="small"
                :scroll="{ x: 600 }"
              >
                <template slot="type" slot-scope="text">
                  <a-tag :color="getTradeTypeColor(text)">
                    {{ getTradeTypeText(text) }}
                  </a-tag>
                </template>
                <template slot="balance" slot-scope="text">
                  <span style="color: #1890ff; font-weight: 500;">
                    ${{ text ? text.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--' }}
                  </span>
                </template>
                <template slot="profit" slot-scope="text">
                  <span :style="{ color: text > 0 ? '#52c41a' : text < 0 ? '#f5222d' : '#666' }">
                    {{ formatMoney(text) }}
                  </span>
                </template>
              </a-table>
            </div>
          </div>

          <!-- 加载状态 - 增强版动画 -->
          <div v-if="loading" class="loading-overlay">
            <div class="loading-content">
              <div class="loading-animation">
                <div class="chart-bars">
                  <div class="bar bar1"></div>
                  <div class="bar bar2"></div>
                  <div class="bar bar3"></div>
                  <div class="bar bar4"></div>
                  <div class="bar bar5"></div>
                </div>
              </div>
              <div class="loading-text">{{ $t('dashboard.indicator.backtest.running') }}</div>
              <div class="loading-subtext">{{ loadingTip }}</div>
            </div>
          </div>
        </a-tab-pane>

        <a-tab-pane key="ai" :tab="$t('dashboard.indicator.backtest.tabAI') || 'AI Agent'">
          <div class="ai-agent-panel">
            <!-- Config Form -->
            <a-form layout="inline" style="margin-bottom: 16px;">
              <a-form-item :label="$t('dashboard.indicator.backtest.targetMetric') || 'Target Metric'">
                <a-select v-model="agent.config.targetMetric" style="width: 150px">
                  <a-select-option value="totalReturn">Total Return</a-select-option>
                  <a-select-option value="sharpeRatio">Sharpe Ratio</a-select-option>
                  <a-select-option value="winRate">Win Rate</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item :label="$t('dashboard.indicator.backtest.maxIterations') || 'Max Iterations'">
                <a-input-number v-model="agent.config.maxIterations" :min="1" :max="50" />
              </a-form-item>
              <a-form-item :label="$t('dashboard.indicator.backtest.model') || 'AI Model'">
                <a-select v-model="agent.config.model" style="width: 200px">
                  <a-select-option v-for="m in modelList" :key="m.value" :value="m.value">
                    {{ m.label }}
                  </a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item>
                <a-button icon="upload" @click="handleImportParams" style="margin-right: 8px">{{ $t('dashboard.indicator.backtest.importConfig') || 'Import Config' }}</a-button>
              </a-form-item>
              <a-form-item>
                <a-button type="primary" :loading="agent.loading || agent.status === 'running'" @click="handleAgentStart">
                  {{ agent.status === 'running' ? ($t('dashboard.indicator.backtest.running') || 'Running...') : ($t('dashboard.indicator.backtest.startOpt') || 'Start Optimization') }}
                </a-button>
                <a-button v-if="agent.status === 'running'" type="danger" style="margin-left: 8px" @click="handleAgentControl('stop')">{{ $t('dashboard.indicator.backtest.stop') || 'Stop' }}</a-button>
                <a-divider type="vertical" />
                <a-button v-if="['completed', 'cancelled'].includes(agent.status) && agent.bestResult" icon="download" @click="exportAgentBestConfig">{{ $t('dashboard.indicator.backtest.exportBest') || '导出最佳配置' }}</a-button>
              </a-form-item>
            </a-form>

            <!-- Imported Config Display -->
            <div v-if="agent.importedConfig" class="imported-config-card" style="background:#e6f7ff; border:1px solid #91d5ff; padding:12px; margin-bottom:16px; border-radius:4px;">
              <strong>📋 已导入配置</strong>
              <div style="margin-top:8px; font-size:12px;">
                <a-row :gutter="8">
                  <a-col :span="8" v-if="agent.importedConfig.initialCapital">
                    <a-tag>初始资金: ${{ agent.importedConfig.initialCapital.toLocaleString() }}</a-tag>
                  </a-col>
                  <a-col :span="8" v-if="agent.importedConfig.commission !== undefined">
                    <a-tag>手续费: {{ (agent.importedConfig.commission * 100).toFixed(2) }}%</a-tag>
                  </a-col>
                  <a-col :span="8" v-if="agent.importedConfig.leverage">
                    <a-tag>杠杆: {{ agent.importedConfig.leverage }}x</a-tag>
                  </a-col>
                </a-row>
                <a-row :gutter="8" style="margin-top:8px;">
                  <a-col :span="8" v-if="agent.importedConfig.stopLossPct !== undefined">
                    <a-tag color="red">止损: {{ agent.importedConfig.stopLossPct.toFixed(2) }}%</a-tag>
                  </a-col>
                  <a-col :span="8" v-if="agent.importedConfig.takeProfitPct !== undefined">
                    <a-tag color="green">止盈: {{ agent.importedConfig.takeProfitPct.toFixed(2) }}%</a-tag>
                  </a-col>
                  <a-col :span="8" v-if="agent.importedConfig.entryPct !== undefined">
                    <a-tag color="blue">开仓资金: {{ agent.importedConfig.entryPct.toFixed(2) }}%</a-tag>
                  </a-col>
                </a-row>
              </div>
            </div>

            <!-- Progress -->
            <div v-if="agent.jobId" style="margin-bottom: 16px;">
              <div style="display:flex; justify-content:space-between; margin-bottom: 8px;">
                <span>Status: <a-tag :color="agent.status === 'running' ? 'blue' : agent.status === 'completed' ? 'green' : 'default'">{{ agent.status }}</a-tag></span>
                <span>Iteration: {{ agent.currentIteration }} / {{ agent.maxIterations }}</span>
              </div>
              <a-progress :percent="Math.floor((agent.currentIteration / agent.maxIterations) * 100)" status="active" />
            </div>

            <!-- Best Result -->
            <div v-if="agent.bestResult" class="best-result-card" style="background:#f6ffed; border:1px solid #b7eb8f; padding:12px; margin-bottom:16px; border-radius:4px;">
              <strong>🏆 Best Result So Far:</strong>
              <div style="margin-top:8px;">
                <a-tag color="green">Total Return: {{ (agent.bestResult.metrics.totalReturn * 100).toFixed(2) }}%</a-tag>
                <a-tag color="blue">Sharpe: {{ (agent.bestResult.metrics.sharpeRatio || 0).toFixed(2) }}</a-tag>
                <a-tag>Win Rate: {{ (agent.bestResult.metrics.winRate * 100).toFixed(2) }}%</a-tag>
              </div>
              <div style="font-size:12px; color:#666; margin-top:8px;">
                Params: {{ JSON.stringify(agent.bestResult.params) }}
              </div>
            </div>

            <!-- Logs -->
            <div class="agent-logs" style="background:#1e1e1e; color:#eee; padding:12px; height:300px; overflow-y:auto; font-family:monospace; font-size:12px; border-radius:4px;">
              <div v-for="(log, index) in agent.logs" :key="index">{{ log }}</div>
              <div v-if="agent.logs.length === 0" style="color:#666; text-align:center; margin-top:100px;">Waiting for logs...</div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <template slot="footer">
      <div style="display:flex; justify-content: space-between; align-items:center; width: 100%;">
        <div>
          <a-button v-if="activeTab === 'manual' && currentStep > 0" :disabled="loading" @click="handlePrev">{{ $t('dashboard.indicator.backtest.prev') }}</a-button>
        </div>
        <div>
          <a-button :disabled="loading" @click="handleCancel">{{ $t('dashboard.indicator.backtest.close') }}</a-button>

          <template v-if="activeTab === 'manual'">
            <a-button
              v-if="currentStep < 1"
              type="primary"
              style="margin-left: 8px;"
              :disabled="loading"
              @click="handleNext"
            >{{ $t('dashboard.indicator.backtest.next') }}</a-button>

            <!-- Import/Export Buttons -->
            <a-button
              v-if="currentStep === 0"
              icon="upload"
              style="margin-left: 8px;"
              @click="handleImportParams"
            >
              {{ $t('dashboard.indicator.backtest.importConfig') || 'Import Config' }}
            </a-button>
            <a-button
              v-if="currentStep === 0"
              icon="download"
              style="margin-left: 8px;"
              @click="handleExportParams"
            >
              {{ $t('dashboard.indicator.backtest.exportConfig') || 'Export Config' }}
            </a-button>

            <a-button
              v-if="currentStep === 1"
              type="primary"
              style="margin-left: 8px;"
              :loading="loading"
              @click="handleRunBacktest"
            >{{ $t('dashboard.indicator.backtest.run') }}</a-button>
            <a-button
              v-if="currentStep > 1"
              type="primary"
              style="margin-left: 8px;"
              :disabled="loading"
              @click="handleRerun"
            >{{ $t('dashboard.indicator.backtest.rerun') }}</a-button>
          </template>
        </div>
      </div>
      <!-- Common File Input -->
      <input
        type="file"
        ref="fileInput"
        accept=".json"
        style="display: none"
        @change="onFileSelected"
      />
    </template>
  </a-modal>
</template>

<script>
import moment from 'moment'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { startAgentOptimization, controlAgentJob, getAgentJobStatus } from '@/api/backtest'
import { DEFAULT_AI_MODEL_MAP, modelMapToOptions } from '@/config/aiModels'

export default {
  name: 'BacktestModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    userId: {
      type: [Number, String],
      default: 1
    },
    indicator: {
      type: Object,
      default: null
    },
    symbol: {
      type: String,
      default: ''
    },
    market: {
      type: String,
      default: ''
    },
    timeframe: {
      type: String,
      default: '1D'
    }
  },
  data () {
    return {
      activeTab: 'manual', // manual | ai
      // AI Agent State
      agent: {
        config: {
          maxIterations: 10,
          targetMetric: 'totalReturn', // totalReturn, sharpeRatio, winRate
          model: 'deepseek-chat',
          strategyCode: '' // Optional for Phase 2
        },
        jobId: null,
        status: 'idle', // idle, pending, running, paused, completed, cancelled, error
        currentIteration: 0,
        maxIterations: 10,
        logs: [],
        bestResult: null,
        importedConfig: null, // Store imported configuration for display
        error: null,
        loading: false
      },
      agentTimer: null,

      form: this.$form.createForm(this),
      loading: false,
      loadingTip: '',
      loadingTimer: null,
      currentStep: 0,
      hasResult: false,
      backtestRunId: null,
      step1CollapseKeys: ['risk'],
      // Step1 UI state (Ant Form getFieldValue is not reactive)
      trailingEnabledUi: false,
      entryPctMaxUi: 100,
      precisionInfo: null, // 回测精度信息
      selectedDatePreset: null, // 当前选中的快捷日期
      selectedTimeframe: '1D', // 用户选择的时间周期（默认使用props传入的值）
      result: {
        totalReturn: 0,
        annualReturn: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        winRate: 0,
        profitFactor: 0,
        totalTrades: 0,
        totalProfit: 0,
        totalCommission: 0,
        trades: [],
        equityCurve: []
      },
      equityChart: null,

      tradeColumns: [],
      modelList: modelMapToOptions(DEFAULT_AI_MODEL_MAP)
    }
  },
  computed: {
    // 根据周期计算最大回测时间范围
    maxBacktestRange () {
      // 1分钟线：最多1个月
      const tf = this.selectedTimeframe || this.timeframe || '1D'
      if (tf === '1m') {
        return { days: 30, label: '1个月' }
      }
      // 5分钟线：最多6个月
      if (tf === '5m') {
        return { days: 180, label: '6个月' }
      }
      // 15分钟和30分钟：最多1年
      if (['15m', '30m'].includes(tf)) {
        return { days: 365, label: '1年' }
      }
      // 1小时及以上：最多3年
      return { days: 1095, label: '3年' }
    },
    // 根据时间周期推荐的默认日期范围 - 统一默认30天
    recommendedRange () {
      return { days: 30, label: '30天', key: '30d' }
    },
    // 合并提示框的类型
    combinedAlertType () {
      if (this.precisionInfo && this.precisionInfo.enabled) {
        return this.precisionInfo.precision === 'high' ? 'success' : 'info'
      }
      if (this.precisionInfo && !this.precisionInfo.enabled && this.market && this.market.toLowerCase() === 'crypto') {
        return 'warning'
      }
      return 'info'
    },
    // 快捷日期选项 - 所有周期都包含30天作为默认选项
    datePresets () {
      const presets = []
      const tf = this.selectedTimeframe || this.timeframe || '1D'
      // 根据时间周期动态生成合理的快捷选项
      // 使用国际通用格式：7D, 14D, 30D, 3M, 6M, 1Y
      if (tf === '1m') {
        presets.push({ key: '7d', days: 7, label: '7D' })
        presets.push({ key: '14d', days: 14, label: '14D' })
        presets.push({ key: '30d', days: 30, label: '30D' })
      } else if (tf === '5m') {
        presets.push({ key: '14d', days: 14, label: '14D' })
        presets.push({ key: '30d', days: 30, label: '30D' })
        presets.push({ key: '90d', days: 90, label: '3M' })
        presets.push({ key: '180d', days: 180, label: '6M' })
      } else if (['15m', '30m'].includes(tf)) {
        presets.push({ key: '30d', days: 30, label: '30D' })
        presets.push({ key: '90d', days: 90, label: '3M' })
        presets.push({ key: '180d', days: 180, label: '6M' })
        presets.push({ key: '365d', days: 365, label: '1Y' })
      } else {
        // 1H, 4H, 1D, 1W
        presets.push({ key: '30d', days: 30, label: '30D' })
        presets.push({ key: '90d', days: 90, label: '3M' })
        presets.push({ key: '180d', days: 180, label: '6M' })
        presets.push({ key: '365d', days: 365, label: '1Y' })
      }
      return presets
    },
    defaultStartDate () {
      // 默认开始日期：使用推荐范围
      return moment().subtract(this.recommendedRange.days, 'days')
    },
    defaultEndDate () {
      // 默认结束日期：今天
      return moment()
    },
    // 最早可选日期
    earliestDate () {
      return moment().subtract(this.maxBacktestRange.days, 'days')
    },
    labelCol () {
      // Wider label area in Step 1 to avoid overlap with inputs
      if (this.currentStep === 0) return { span: 9 }
      return { span: 6 }
    },
    wrapperCol () {
      if (this.currentStep === 0) return { span: 15 }
      return { span: 18 }
    }
    // entryPctMaxUi is in data (percent units)
  },
  watch: {
    visible (val) {
      if (val) {
        // 弹窗打开时重置状态
        this.currentStep = 0
        this.hasResult = false
        this.backtestRunId = null
        this.step1CollapseKeys = ['risk']
        this.trailingEnabledUi = false
        this.entryPctMaxUi = 100
        this.precisionInfo = null
        this.selectedDatePreset = null
        this.selectedTimeframe = this.timeframe || '1D' // 初始化为props传入的时间周期
        this.result = {
          totalReturn: 0,
          annualReturn: 0,
          maxDrawdown: 0,
          sharpeRatio: 0,
          winRate: 0,
          profitFactor: 0,
          totalTrades: 0,
          totalProfit: 0,
          totalCommission: 0,
          trades: [],
          equityCurve: []
        }
        this.$nextTick(() => {
          if (this.form) {
            this.form.resetFields()
            // Sync non-reactive form values into UI state
            this.trailingEnabledUi = !!this.form.getFieldValue('trailingEnabled')
            this.recalcEntryPctMaxUi()
            // 默认选中30天
            this.selectedDatePreset = '30d'
            // 弹窗打开时立即获取精度信息（使用默认日期范围）
            this.fetchPrecisionInfo()
          }
        })
      } else {
        // 弹窗关闭时销毁图表
        if (this.equityChart) {
          this.equityChart.dispose()
          this.equityChart = null
        }
      }
    }
  },
  created () {
    // 初始化表格列（需要在created中初始化才能使用$t）
    this.tradeColumns = [
      {
        title: this.$t('dashboard.indicator.backtest.tradeTime'),
        dataIndex: 'time',
        key: 'time',
        width: 160
      },
      {
        title: this.$t('dashboard.indicator.backtest.tradeType'),
        dataIndex: 'type',
        key: 'type',
        width: 120,
        scopedSlots: { customRender: 'type' }
      },
      {
        title: this.$t('dashboard.indicator.backtest.price'),
        dataIndex: 'price',
        key: 'price',
        width: 110
      },
      {
        title: this.$t('dashboard.indicator.backtest.amount'),
        dataIndex: 'amount',
        key: 'amount',
        width: 100,
        customRender: (text) => {
          return text ? text.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : '--'
        }
      },
      {
        title: this.$t('dashboard.indicator.backtest.profit'),
        dataIndex: 'profit',
        key: 'profit',
        width: 110,
        scopedSlots: { customRender: 'profit' }
      },
      {
        title: this.$t('dashboard.indicator.backtest.balance'),
        dataIndex: 'balance',
        key: 'balance',
        width: 130,
        scopedSlots: { customRender: 'balance' }
      }
    ]
  },
  methods: {
    // --- Step 1 UX helpers ---
    recalcEntryPctMaxUi () {
      if (!this.form) {
        this.entryPctMaxUi = 100
        return
      }
      const trendOn = !!this.form.getFieldValue('trendAddEnabled')
      const dcaOn = !!this.form.getFieldValue('dcaAddEnabled')
      const trendTimes = Number(this.form.getFieldValue('trendAddMaxTimes') || 0)
      const dcaTimes = Number(this.form.getFieldValue('dcaAddMaxTimes') || 0)
      const trendSizePct = Number(this.form.getFieldValue('trendAddSizePct') || 0) // percent
      const dcaSizePct = Number(this.form.getFieldValue('dcaAddSizePct') || 0) // percent

      const reservePct = (trendOn ? trendTimes * trendSizePct : 0) + (dcaOn ? dcaTimes * dcaSizePct : 0)
      const maxEntryPct = Math.max(0, Math.min(100, 100 - reservePct))
      this.entryPctMaxUi = maxEntryPct
    },
    normalizeEntryPct () {
      if (!this.form) return
      const current = Number(this.form.getFieldValue('entryPct') || 0)
      const max = Number(this.entryPctMaxUi || 100)
      if (current > max) {
        this.form.setFieldsValue({ entryPct: max })
      }
    },
    onTrendAddToggle (checked) {
      if (!this.form) return
      // Mutual exclusion to avoid double scale-in on the same candle.
      if (checked) {
        this.form.setFieldsValue({ dcaAddEnabled: false })
      }
      this.$nextTick(() => {
        this.recalcEntryPctMaxUi()
        this.normalizeEntryPct()
      })
    },
    onDcaAddToggle (checked) {
      if (!this.form) return
      if (checked) {
        this.form.setFieldsValue({ trendAddEnabled: false })
      }
      this.$nextTick(() => {
        this.recalcEntryPctMaxUi()
        this.normalizeEntryPct()
      })
    },
    onScaleParamsChange () {
      this.$nextTick(() => {
        this.recalcEntryPctMaxUi()
        this.normalizeEntryPct()
      })
    },
    onEntryPctChange () {
      this.$nextTick(() => this.normalizeEntryPct())
    },
    onTrailingToggle (checked) {
      if (!this.form) return
      this.trailingEnabledUi = !!checked
      // Only show fields when enabled; also clear values when disabled.
      if (!checked) {
        this.form.setFieldsValue({ trailingStopPct: 0, trailingActivationPct: 0 })
      }
    },
    // 获取交易类型颜色
    getTradeTypeColor (type) {
      const colorMap = {
        // 旧格式
        'buy': 'green',
        'sell': 'red',
        'liquidation': 'orange',
        // 新格式 - 做多
        'open_long': 'green',
        'add_long': 'cyan',
        'close_long': 'orange',
        'close_long_stop': 'red',
        'close_long_profit': 'lime',
        'close_long_trailing': 'gold',
        'reduce_long': 'volcano',
        // 新格式 - 做空
        'open_short': 'red',
        'add_short': 'magenta',
        'close_short': 'blue',
        'close_short_stop': 'red',
        'close_short_profit': 'cyan',
        'close_short_trailing': 'gold',
        'reduce_short': 'volcano'
      }
      return colorMap[type] || 'default'
    },
    // 获取交易类型文本
    getTradeTypeText (type) {
      const textMap = {
        // 旧格式
        'buy': this.$t('dashboard.indicator.backtest.buy'),
        'sell': this.$t('dashboard.indicator.backtest.sell'),
        'liquidation': this.$t('dashboard.indicator.backtest.liquidation'),
        // 新格式 - 做多
        'open_long': this.$t('dashboard.indicator.backtest.openLong'),
        'add_long': this.$t('dashboard.indicator.backtest.addLong'),
        'close_long': this.$t('dashboard.indicator.backtest.closeLong'),
        'close_long_stop': this.$t('dashboard.indicator.backtest.closeLongStop'),
        'close_long_profit': this.$t('dashboard.indicator.backtest.closeLongProfit'),
        'close_long_trailing': this.$t('dashboard.indicator.backtest.closeLongTrailing'),
        'reduce_long': this.$t('dashboard.indicator.backtest.reduceLong'),
        // 新格式 - 做空
        'open_short': this.$t('dashboard.indicator.backtest.openShort'),
        'add_short': this.$t('dashboard.indicator.backtest.addShort'),
        'close_short': this.$t('dashboard.indicator.backtest.closeShort'),
        'close_short_stop': this.$t('dashboard.indicator.backtest.closeShortStop'),
        'close_short_profit': this.$t('dashboard.indicator.backtest.closeShortProfit'),
        'close_short_trailing': this.$t('dashboard.indicator.backtest.closeShortTrailing'),
        'reduce_short': this.$t('dashboard.indicator.backtest.reduceShort')
      }
      return textMap[type] || type
    },
    disabledStartDate (current) {
      if (!current) return false
      // 不能选择今天之后的日期
      if (current > moment().endOf('day')) return true
      // 不能选择最早日期之前的日期
      if (current < this.earliestDate.startOf('day')) return true
      return false
    },
    disabledEndDate (current) {
      if (!current) return false
      // 不能选择今天之后的日期
      if (current > moment().endOf('day')) return true
      // 不能选择最早日期之前的日期
      if (current < this.earliestDate.startOf('day')) return true

      // 如果已选择开始日期，限制结束日期不能超过开始日期+最大回测范围
      const startDate = this.form.getFieldValue('startDate')
      if (startDate) {
        const maxDays = this.maxBacktestRange.days || 365
        const maxEndDate = moment(startDate).add(maxDays, 'days')
        if (current > maxEndDate.endOf('day')) return true
      }

      return false
    },
    // 应用快捷日期选择
    applyDatePreset (preset) {
      this.selectedDatePreset = preset.key
      const endDate = moment()
      const startDate = moment().subtract(preset.days, 'days')
      this.form.setFieldsValue({
        startDate: startDate,
        endDate: endDate
      })
      // 更新精度信息
      this.fetchPrecisionInfo(startDate, endDate)
    },
    // 获取精度信息
    async fetchPrecisionInfo (startDate, endDate) {
      // 如果没有传入日期，尝试从表单获取或使用默认值
      if (!startDate || !endDate) {
        startDate = this.form ? this.form.getFieldValue('startDate') : null
        endDate = this.form ? this.form.getFieldValue('endDate') : null
      }
      // 如果还是没有，使用默认值
      if (!startDate) startDate = this.defaultStartDate
      if (!endDate) endDate = this.defaultEndDate

      // 仅加密货币市场支持高精度回测
      if (!this.market || this.market.toLowerCase() !== 'crypto') {
        this.precisionInfo = {
          enabled: false,
          reason: 'only_crypto',
          message: this.$t('dashboard.indicator.backtest.onlyCryptoSupported')
        }
        return
      }

      try {
        const response = await request({
          url: '/api/indicator/backtest/precision-info',
          method: 'post',
          data: {
            market: this.market,
            startDate: startDate.format('YYYY-MM-DD'),
            endDate: endDate.format('YYYY-MM-DD')
          }
        })

        if (response.code === 1 && response.data) {
          this.precisionInfo = response.data
        }
      } catch (e) {
        // 静默失败，不影响正常使用
        this.precisionInfo = null
      }
    },
    // 时间周期变化时重新获取精度信息和更新快捷日期选项
    onTimeframeChange () {
      // 重置日期选择为默认30天
      this.selectedDatePreset = '30d'
      const endDate = moment()
      const startDate = moment().subtract(30, 'days')
      this.form.setFieldsValue({
        startDate: startDate,
        endDate: endDate
      })
      // 重新获取精度信息
      this.fetchPrecisionInfo(startDate, endDate)
    },
    // 日期变化时获取精度信息
    onDateChange () {
      this.selectedDatePreset = null // 清除快捷选择状态
      this.$nextTick(() => {
        this.fetchPrecisionInfo()
      })
    },
    // 验证日期范围
    validateDateRange (startDate, endDate) {
      if (!startDate || !endDate) return true
      const diffDays = endDate.diff(startDate, 'days')
      const maxDays = this.maxBacktestRange.days || 365
      if (diffDays > maxDays) {
        this.$message.error(this.$t('dashboard.indicator.backtest.dateRangeExceededDays', {
          timeframe: this.selectedTimeframe || this.timeframe,
          maxRange: this.maxBacktestRange.label,
          maxDays
        }))
        return false
      }
      return true
    },
    formatPercent (value) {
      if (value === null || value === undefined) return '--'
      // 后端返回的已经是百分比数值（如59.34表示59.34%），不需要再乘100
      const sign = value >= 0 ? '+' : ''
      return `${sign}${value.toFixed(2)}%`
    },
    formatMoney (value) {
      if (value === null || value === undefined) return '--'
      // 正数显示+，负数显示-
      const sign = value >= 0 ? '+' : '-'
      return `${sign}$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    },
    handleCancel () {
      this.$emit('cancel')
    },
    handlePrev () {
      if (this.loading) return
      if (this.currentStep > 0) this.currentStep -= 1
    },
    handleNext () {
      if (this.loading) return
      if (this.currentStep === 0) {
        // Step 1 has no required fields; proceed directly.
        this.currentStep = 1
        return
      }
      if (this.currentStep === 1) {
        // Normally Step 2 uses Run button; keep this for completeness.
        this.handleRunBacktest()
      }
    },
    handleRerun () {
      if (this.loading) return
      // Go back to Step 2 so user can adjust settings then run again.
      this.currentStep = 1
      this.hasResult = false
      this.backtestRunId = null
    },
    // 加载动画提示轮播
    startLoadingAnimation () {
      const tips = [
        this.$t('dashboard.indicator.backtest.loadingTip1') || '正在获取历史K线数据...',
        this.$t('dashboard.indicator.backtest.loadingTip2') || '正在执行策略信号计算...',
        this.$t('dashboard.indicator.backtest.loadingTip3') || '正在模拟交易执行...',
        this.$t('dashboard.indicator.backtest.loadingTip4') || '正在计算回测指标...',
        this.$t('dashboard.indicator.backtest.loadingTip5') || '即将完成，请稍候...'
      ]
      let idx = 0
      this.loadingTip = tips[0]
      this.loadingTimer = setInterval(() => {
        idx = (idx + 1) % tips.length
        this.loadingTip = tips[idx]
      }, 2000)
    },
    stopLoadingAnimation () {
      this.loading = false
      if (this.loadingTimer) {
        clearInterval(this.loadingTimer)
        this.loadingTimer = null
      }
    },
    // --- Inline Helper Methods ---
    ensureIOUtils (callback) {
      if (window.BacktestUtils) {
        callback()
        return
      }
      const script = document.createElement('script')
      script.src = '/js/backtest-utils.js'
      script.onload = () => {
        setTimeout(callback, 50)
      }
      script.onerror = () => {
        this.$message.error('Failed to load IO utility')
      }
      document.body.appendChild(script)
    },
    doExportConfig (data) {
       const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
       const filename = `backtest_config_${dateStr}.json`

       this.ensureIOUtils(() => {
         if (window.BacktestUtils && window.BacktestUtils.exportConfig) {
           const success = window.BacktestUtils.exportConfig(data, filename)
           if (!success) {
             this.$message.error(this.$t('dashboard.indicator.backtest.exportFailed') || 'Export failed')
           }
         } else {
           this.$message.error('IO Utils not initialized')
         }
       })
    },
    doImportConfig (file, successCallback) {
      this.ensureIOUtils(() => {
        if (window.BacktestUtils && window.BacktestUtils.readConfig) {
          window.BacktestUtils.readConfig(file, (err, data) => {
            if (err) {
              console.error(err)
              this.$message.error(this.$t('dashboard.indicator.backtest.importFailed') || 'Import failed')
            } else {
              successCallback(data)
            }
          })
        }
      })
    },
    // --- End Inline Helper Methods ---

    handleExportParams () {
      try {
        const formValues = this.form.getFieldsValue()

        // Prepare data
        const exportData = {
          ...formValues,
          _uiState: {
            trailingEnabledUi: this.trailingEnabledUi,
            step1CollapseKeys: this.step1CollapseKeys,
            entryPctMaxUi: this.entryPctMaxUi,
            selectedDatePreset: this.selectedDatePreset,
            selectedTimeframe: this.selectedTimeframe,
            precisionInfo: this.precisionInfo
          }
        }

        // Convert Dates
        if (exportData.startDate && exportData.startDate.toISOString) {
          exportData.startDate = exportData.startDate.toISOString()
        }
        if (exportData.endDate && exportData.endDate.toISOString) {
          exportData.endDate = exportData.endDate.toISOString()
        }

        this.doExportConfig(exportData)
      } catch (e) {
        console.error(e)
        this.$message.error(this.$t('dashboard.indicator.backtest.exportFailed') || 'Export failed')
      }
    },
    handleImportParams () {
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
        this.$refs.fileInput.click()
      }
    },
    onFileSelected (e) {
      const file = e.target.files[0]
      if (!file) return

      this.doImportConfig(file, (data) => {
         try {
             // Restore UI state
             const uiState = data._uiState || {}
             delete data._uiState

             // 1. Sync UI Flags
             if (uiState.trailingEnabledUi !== undefined) {
                 this.trailingEnabledUi = uiState.trailingEnabledUi
             } else if (data.trailingEnabled !== undefined) {
                 // Fallback: infer from data if _uiState missing
                 this.trailingEnabledUi = !!data.trailingEnabled
             }

             if (uiState.step1CollapseKeys) this.step1CollapseKeys = uiState.step1CollapseKeys
             if (uiState.entryPctMaxUi) this.entryPctMaxUi = uiState.entryPctMaxUi
             if (uiState.selectedDatePreset) this.selectedDatePreset = uiState.selectedDatePreset
             if (uiState.selectedTimeframe) this.selectedTimeframe = uiState.selectedTimeframe
             if (uiState.precisionInfo) this.precisionInfo = uiState.precisionInfo

             // Restore Dates
             if (data.startDate) data.startDate = moment(data.startDate)
             if (data.endDate) data.endDate = moment(data.endDate)

             // 2. Wait for UI to render (v-if fields) then set values
             this.$nextTick(() => {
                 this.form.setFieldsValue(data)
                 this.$message.success(this.$t('dashboard.indicator.backtest.importSuccess') || 'Configuration loaded')

                 // Reactivity & Defaults
                 this.recalcEntryPctMaxUi()
                 if (data.startDate && data.endDate) {
                    this.fetchPrecisionInfo(data.startDate, data.endDate)
                 }

                 // Save imported config for AI tab display
                 this.agent.importedConfig = { ...data }

                 // Format dates
                 if (data.startDate) {
                    this.agent.importedConfig.startDate = moment(data.startDate).format('YYYY-MM-DD')
                 }
                 if (data.endDate) {
                    this.agent.importedConfig.endDate = moment(data.endDate).format('YYYY-MM-DD')
                 }
             })
          } catch (err) {
             console.error(err)
             this.$message.error('Error applying configuration')
          }
       })

      e.target.value = ''
    },
    async handleRunBacktest () {
      // Only validate Step 2 fields (dates/capital/fees/etc.)
      const step2Fields = ['startDate', 'endDate', 'initialCapital', 'commission', 'leverage', 'tradeDirection', 'slippage']
      this.form.validateFields(step2Fields, async (err, values) => {
        if (err) return

        // IMPORTANT:
        // validateFields(step2Fields) only returns those fields' values.
        // Strategy/risk params are in Step 1, so we must also read all form values,
        // otherwise stopLoss/takeProfit/trailing configs will be missing (defaulting to 0).
        const allValues = { ...(this.form.getFieldsValue() || {}), ...(values || {}) }

        if (!this.indicator || !this.indicator.id) {
          this.$message.error(this.$t('dashboard.indicator.backtest.noIndicatorCode'))
          return
        }

        if (!this.symbol) {
          this.$message.error(this.$t('dashboard.indicator.backtest.noSymbol'))
          return
        }

        // Validate date range
        if (!this.validateDateRange(values.startDate, values.endDate)) {
          return
        }

        this.loading = true
        this.hasResult = false
        this.startLoadingAnimation()

        try {
          const pct = (v) => Number(v || 0) / 100
          const strategyConfig = {
            risk: {
              stopLossPct: pct(allValues.stopLossPct),
              takeProfitPct: pct(allValues.takeProfitPct),
              trailing: {
                enabled: !!allValues.trailingEnabled,
                pct: pct(allValues.trailingStopPct),
                activationPct: pct(allValues.trailingActivationPct)
              }
            },
            position: {
              entryPct: pct(allValues.entryPct || 0)
            },
            scale: {
              trendAdd: {
                enabled: !!allValues.trendAddEnabled,
                stepPct: pct(allValues.trendAddStepPct),
                sizePct: pct(allValues.trendAddSizePct),
                maxTimes: allValues.trendAddMaxTimes || 0
              },
              dcaAdd: {
                enabled: !!allValues.dcaAddEnabled,
                stepPct: pct(allValues.dcaAddStepPct),
                sizePct: pct(allValues.dcaAddSizePct),
                maxTimes: allValues.dcaAddMaxTimes || 0
              },
              trendReduce: {
                enabled: !!allValues.trendReduceEnabled,
                stepPct: pct(allValues.trendReduceStepPct),
                sizePct: pct(allValues.trendReduceSizePct),
                maxTimes: allValues.trendReduceMaxTimes || 0
              },
              adverseReduce: {
                enabled: !!allValues.adverseReduceEnabled,
                stepPct: pct(allValues.adverseReduceStepPct),
                sizePct: pct(allValues.adverseReduceSizePct),
                maxTimes: allValues.adverseReduceMaxTimes || 0
              }
            }
          }

          const requestData = {
            userid: this.userId || 1,
            indicatorId: this.indicator.id,
            symbol: this.symbol,
            market: this.market,
            timeframe: this.selectedTimeframe || this.timeframe,
            startDate: values.startDate.format('YYYY-MM-DD'),
            endDate: values.endDate.format('YYYY-MM-DD'),
            initialCapital: values.initialCapital,
            commission: pct(values.commission || 0),
            slippage: pct(values.slippage || 0),
            leverage: values.leverage || 1,
            tradeDirection: values.tradeDirection || 'long',
            strategyConfig,
            // 启用多时间框架高精度回测（加密货币市场）
            enableMtf: this.market && this.market.toLowerCase() === 'crypto'
          }

          const response = await request({
            url: '/api/indicator/backtest',
            method: 'post',
            data: requestData
          })

          if (response.code === 1 && response.data) {
            // Backward compatible: data can be { runId, result } or raw result
            if (response.data.runId) {
              this.backtestRunId = response.data.runId
            }
            this.result = response.data.result || response.data
            this.hasResult = true
            this.currentStep = 2
            this.$nextTick(() => {
              this.renderEquityChart()
            })
            this.$message.success(this.$t('dashboard.indicator.backtest.success'))
          } else {
            this.$message.error(response.msg || this.$t('dashboard.indicator.backtest.failed'))
          }
        } catch (error) {
          this.$message.error(this.$t('dashboard.indicator.backtest.failed'))
        } finally {
          this.stopLoadingAnimation()
          this.loading = false
        }
      })
    },
    renderEquityChart () {
      if (!this.$refs.equityChartRef) return

      if (this.equityChart) {
        this.equityChart.dispose()
      }

      this.equityChart = echarts.init(this.$refs.equityChartRef)

      const data = this.result.equityCurve || []
      // 后端返回格式：{ time: "2025-06-01 00:00", value: 100000 }
      // 前端需要：dates, equity (value字段), benchmark (可选)
      const dates = data.map(item => item.time || item.date)
      const equity = data.map(item => item.value !== undefined ? item.value : item.equity)

      // 计算收益是正还是负，用于渐变颜色
      const initialValue = equity[0] || 100000
      const finalValue = equity[equity.length - 1] || initialValue
      const isPositive = finalValue >= initialValue
      const mainColor = isPositive ? '#52c41a' : '#f5222d'
      const gradientColor = isPositive
        ? [{ offset: 0, color: 'rgba(82, 196, 26, 0.35)' }, { offset: 1, color: 'rgba(82, 196, 26, 0.02)' }]
        : [{ offset: 0, color: 'rgba(245, 34, 45, 0.35)' }, { offset: 1, color: 'rgba(245, 34, 45, 0.02)' }]

      const option = {
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          borderColor: '#e8e8e8',
          borderWidth: 1,
          textStyle: {
            color: '#333'
          },
          formatter: (params) => {
            let result = `<div style="font-weight: 600; margin-bottom: 8px; color: #262626;">${params[0].axisValue}</div>`
            params.forEach(param => {
              if (param.value !== undefined && param.value !== null) {
                const value = param.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                result += `<div style="display: flex; justify-content: space-between; gap: 24px; margin: 4px 0;">
                  <span>${param.marker} ${param.seriesName}</span>
                  <span style="font-weight: 600; color: ${mainColor};">$${value}</span>
                </div>`
              }
            })
            return result
          }
        },
        legend: {
          show: false
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '12%',
          top: '8%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLine: {
            lineStyle: { color: '#e8e8e8' }
          },
          axisTick: { show: false },
          axisLabel: {
            color: '#8c8c8c',
            fontSize: 11,
            rotate: 0,
            interval: Math.floor(dates.length / 6) // 自动间隔显示
          }
        },
        yAxis: {
          type: 'value',
          splitLine: {
            lineStyle: { color: '#f5f5f5', type: 'dashed' }
          },
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: {
            color: '#8c8c8c',
            fontSize: 11,
            formatter: (value) => {
              if (value >= 1000000) {
                return (value / 1000000).toFixed(1) + 'M'
              } else if (value >= 1000) {
                return (value / 1000).toFixed(0) + 'K'
              }
              return value
            }
          }
        },
        series: [
          {
            name: this.$t('dashboard.indicator.backtest.strategy'),
            type: 'line',
            data: equity,
            smooth: 0.4, // 平滑系数，0-1之间，值越大越平滑
            symbol: 'none', // 不显示数据点
            sampling: 'lttb', // 使用 LTTB 算法降采样，保持曲线形状
            lineStyle: {
              width: 2.5,
              color: mainColor,
              cap: 'round',
              join: 'round'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, gradientColor)
            },
            emphasis: {
              lineStyle: { width: 3 }
            }
          }
        ],
        animation: true,
        animationDuration: 800,
        animationEasing: 'cubicOut'
      }

      this.equityChart.setOption(option)

      // 响应式调整
      window.addEventListener('resize', () => {
        if (this.equityChart) {
          this.equityChart.resize()
        }
      })
    },

    // --- AI Agent Methods ---
    async handleAgentStart () {
      if (this.agent.loading || this.agent.status === 'running') return

      // 1. Validate Form (we need config from Step 2 like dates/capital)
      const step2Fields = ['startDate', 'endDate', 'initialCapital', 'commission', 'leverage', 'tradeDirection', 'slippage']
      this.form.validateFields(step2Fields, async (err, values) => {
        if (err) return

        // 2. Prepare Config
        const allValues = { ...(this.form.getFieldsValue() || {}), ...(values || {}) }
        const pct = (v) => Number(v || 0) / 100

        // Initial strategy config (Baseline)
        const config = {
           // Base Context
           userid: this.userId || 1,
           indicatorId: this.indicator.id,
           symbol: this.symbol,
           market: this.market,
           timeframe: this.selectedTimeframe || this.timeframe,
           startDate: values.startDate.format('YYYY-MM-DD'),
           endDate: values.endDate.format('YYYY-MM-DD'),
           initialCapital: values.initialCapital,
           commission: pct(values.commission || 0),
           slippage: pct(values.slippage || 0),
           leverage: values.leverage || 1,
           tradeDirection: values.tradeDirection || 'long',
           enableMtf: this.market && this.market.toLowerCase() === 'crypto',

           // Strategy Params (current UI values as baseline)
           stopLossPct: pct(allValues.stopLossPct),
           takeProfitPct: pct(allValues.takeProfitPct),
           trailingEnabled: !!allValues.trailingEnabled,
           trailingStopPct: pct(allValues.trailingStopPct),
           trailingActivationPct: pct(allValues.trailingActivationPct),

           // Position Scaling Parameters
           trendAddEnabled: !!allValues.trendAddEnabled,
           dcaAddEnabled: !!allValues.dcaAddEnabled,
           trendAddStepPct: pct(allValues.trendAddStepPct),
           dcaAddStepPct: pct(allValues.dcaAddStepPct),
           trendAddSizePct: pct(allValues.trendAddSizePct),
           dcaAddSizePct: pct(allValues.dcaAddSizePct),
           trendAddMaxTimes: Number(allValues.trendAddMaxTimes || 0),
           dcaAddMaxTimes: Number(allValues.dcaAddMaxTimes || 0),

           trendReduceEnabled: !!allValues.trendReduceEnabled,
           adverseReduceEnabled: !!allValues.adverseReduceEnabled,
           trendReduceStepPct: pct(allValues.trendReduceStepPct),
           adverseReduceStepPct: pct(allValues.adverseReduceStepPct),
           trendReduceSizePct: pct(allValues.trendReduceSizePct),
           adverseReduceSizePct: pct(allValues.adverseReduceSizePct),
           trendReduceMaxTimes: Number(allValues.trendReduceMaxTimes || 0),
           adverseReduceMaxTimes: Number(allValues.adverseReduceMaxTimes || 0),

           entryPct: pct(allValues.entryPct || 100)
        }

        this.agent.loading = true
        this.agent.logs = []
        this.agent.error = null
        this.agent.status = 'pending'

        try {
          const res = await startAgentOptimization({
             config: config,
             strategy_code: this.code || (this.indicator && this.indicator.code) || '',
             target_metric: this.agent.config.targetMetric,
             max_iterations: this.agent.config.maxIterations,
             model: this.agent.config.model
          })

          if (res.job_id) {
             this.agent.jobId = res.job_id
             this.agent.status = 'running'
             this.startAgentPolling()
             this.$message.success('Optimization started')
          } else {
             this.$message.error('Failed to start optimization')
             this.agent.status = 'error'
          }
        } catch (e) {
          console.error(e)
          this.$message.error('Error starting agent')
          this.agent.status = 'error'
        } finally {
          this.agent.loading = false
        }
      })
    },

    async handleAgentControl (action) {
       if (!this.agent.jobId) return
       try {
         await controlAgentJob(this.agent.jobId, action)
         if (action === 'stop') {
            this.stopAgentPolling()
            this.agent.status = 'cancelled'
         }
         this.$message.success(`Job ${action} successful`)
       } catch (e) {
         this.$message.error(`Failed to ${action} job`)
       }
    },

    startAgentPolling () {
       if (this.agentTimer) clearInterval(this.agentTimer)
       this.agentTimer = setInterval(this.pollAgentStatus, 2000)
    },

    stopAgentPolling () {
       if (this.agentTimer) {
         clearInterval(this.agentTimer)
         this.agentTimer = null
       }
    },

    async pollAgentStatus () {
       if (!this.agent.jobId) return
       try {
         const res = await getAgentJobStatus(this.agent.jobId)
         if (res && !res.error) {
            this.agent.status = res.status
            this.agent.currentIteration = res.current_iteration
            this.agent.maxIterations = res.max_iterations
            this.agent.logs = res.logs || []

            if (res.best_result) {
               this.agent.bestResult = res.best_result
            }

            if (['completed', 'cancelled', 'failed'].includes(res.status)) {
               this.stopAgentPolling()
               if (res.status === 'completed') {
                  this.$message.success('Optimization Completed!')
               }
            }
         }
       } catch (e) {
         console.error('Polling error', e)
       }
    },

    exportAgentBestConfig () {
       if (!this.agent.bestResult || !this.agent.bestResult.params) {
           this.$message.warning('暂无最佳配置可导出')
           return
       }

       const p = this.agent.bestResult.params

       // 1. Filter out strategy params and metadata, keep only backtest config params
       const strategyParamKeys = ['rsi_len', 'pivot_window', 'vol_ma_len', 'ob_threshold', 'os_threshold']
       const metadataKeys = ['indicatorId', 'userid', 'symbol', 'market', 'timeframe', 'enableMtf']
       const excludeKeys = [...strategyParamKeys, ...metadataKeys]

       const exportData = {}
       Object.keys(p).forEach(key => {
           if (!excludeKeys.includes(key)) {
               exportData[key] = p[key]
           }
       })

       // Convert dates to strings if needed
       if (exportData.startDate && typeof exportData.startDate === 'object') {
           exportData.startDate = moment(exportData.startDate).format('YYYY-MM-DD')
       }
       if (exportData.endDate && typeof exportData.endDate === 'object') {
           exportData.endDate = moment(exportData.endDate).format('YYYY-MM-DD')
       }

       // Add _uiState to match standard config format
       exportData._uiState = {
           trailingEnabledUi: !!exportData.trailingEnabled,
           step1CollapseKeys: this.step1CollapseKeys || ['risk'],
           entryPctMaxUi: 100,
           selectedDatePreset: this.selectedDatePreset || '30d',
           selectedTimeframe: this.selectedTimeframe || '5m',
           precisionInfo: this.precisionInfo || null
       }

       // Export config file
       try {
           this.doExportConfig(exportData)
           this.$message.success('最佳配置已导出')
       } catch (e) {
           console.error(e)
           this.$message.error('导出配置失败')
           return
       }

       // 2. Ask to update source code (only for strategy params)
       if (this.indicator && this.indicator.id) {
           const strategyParams = {}
           strategyParamKeys.forEach(key => {
               if (p[key] !== undefined) {
                   strategyParams[key] = p[key]
               }
           })

           // Only show dialog if there are strategy params to save
           if (Object.keys(strategyParams).length > 0) {
               this.$confirm({
                   title: this.$t('dashboard.indicator.backtest.saveParamsTitle'),
                   content: this.$t('dashboard.indicator.backtest.saveParamsDesc'),
                   okText: this.$t('common.confirm'),
                   cancelText: this.$t('common.cancel'),
                   onOk: async () => {
                       const loadingMsg = this.$message.loading('正在更新源代码...', 0)
                       try {
                           const res = await request({
                               url: '/api/indicator/update-strategy-params',
                               method: 'post',
                               data: {
                                   userid: this.userId || 1,
                                   indicatorId: this.indicator.id,
                                   params: strategyParams
                               }
                           })
                           loadingMsg()

                           if (res.code === 1) {
                               this.$message.success('源代码已更新')
                               if (res.data && res.data.code) {
                                   // Update local code
                                   this.$emit('update:code', res.data.code)
                                   if (this.indicator) this.indicator.code = res.data.code
                               }
                           } else {
                               this.$message.error(res.msg || '更新失败')
                           }
                       } catch (e) {
                           loadingMsg()
                           console.error(e)
                           this.$message.error('更新失败: ' + (e.message || e))
                       }
                   }
               })
           }
       }
    }
  },
  beforeDestroy () {
    if (this.equityChart) {
      this.equityChart.dispose()
      this.equityChart = null
    }
  }
}
</script>

<style lang="less" scoped>
/* Allow long labels to wrap instead of being visually covered by inputs */
:deep(.ant-form-item-label) {
  white-space: normal;
  line-height: 1.2;
}

:deep(.ant-form-item-label > label) {
  white-space: normal;
}

:deep(.ant-form-item-control) {
  min-width: 0;
}
.backtest-modal {
  :deep(.ant-modal-body) {
    padding: 16px;
    max-height: 70vh;
    overflow-y: auto;
  }
}

.backtest-content {
  position: relative;
}

.field-hint {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.4;
  color: #8c8c8c;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 8px;

  .anticon {
    color: #1890ff;
  }
}

.config-section {
  margin-bottom: 24px;
}

.precision-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.date-quick-select {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.result-section {
  margin-top: 24px;
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;

  @media (max-width: 1200px) {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 992px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 576px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metric-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  &.positive {
    background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
    .metric-value {
      color: #52c41a;
    }
  }

  &.negative {
    background: linear-gradient(135deg, #fff2f0 0%, #ffccc7 100%);
    .metric-value {
      color: #f5222d;
    }
  }

  .metric-label {
    font-size: 12px;
    color: #8c8c8c;
    margin-bottom: 8px;
  }

  .metric-value {
    font-size: 20px;
    font-weight: 700;
    color: #262626;
  }

  .metric-amount {
    font-size: 12px;
    color: #8c8c8c;
    margin-top: 4px;
  }
}

.chart-section {
  margin-bottom: 24px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #595959;
  margin-bottom: 12px;
}

.equity-chart {
  width: 100%;
  height: 300px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.trades-section {
  margin-top: 24px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
  border-radius: 8px;

  .loading-content {
    text-align: center;
  }

  .loading-animation {
    margin-bottom: 20px;
  }

  .chart-bars {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    height: 60px;
    gap: 6px;
  }

  .bar {
    width: 8px;
    background: linear-gradient(180deg, #1890ff 0%, #52c41a 100%);
    border-radius: 4px;
    animation: barPulse 1.2s ease-in-out infinite;
  }

  .bar1 { height: 20px; animation-delay: 0s; }
  .bar2 { height: 35px; animation-delay: 0.1s; }
  .bar3 { height: 50px; animation-delay: 0.2s; }
  .bar4 { height: 35px; animation-delay: 0.3s; }
  .bar5 { height: 20px; animation-delay: 0.4s; }

  @keyframes barPulse {
    0%, 100% { transform: scaleY(1); opacity: 0.7; }
    50% { transform: scaleY(1.5); opacity: 1; }
  }

  .loading-text {
    font-size: 16px;
    font-weight: 500;
    color: #1890ff;
    margin-bottom: 8px;
  }

  .loading-subtext {
    font-size: 13px;
    color: #666;
    animation: fadeInOut 2s ease-in-out infinite;
  }

  @keyframes fadeInOut {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }
}
</style>
