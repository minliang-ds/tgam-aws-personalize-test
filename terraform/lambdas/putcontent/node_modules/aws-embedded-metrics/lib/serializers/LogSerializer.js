"use strict";
/*
 * Copyright 2019 Amazon.com, Inc. or its affiliates.
 * Licensed under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const Constants_1 = require("../Constants");
/**
 * Serializes the provided context to the CWL Structured
 * Logs format with Embedded Metric Filters.
 */
class LogSerializer {
    /**
     * Retrieve the current context as a JSON string
     */
    serialize(context) {
        const dimensionKeys = [];
        let dimensionProperties = {};
        context.getDimensions().forEach(d => {
            // we can only take the first 9 defined dimensions
            // the reason we do this in the serializer is because
            // it is possible that other sinks or formats can
            // support more dimensions
            // in the future it may make sense to introduce a higher-order
            // representation for sink-specific validations
            const keys = Object.keys(d).slice(0, Constants_1.Constants.MAX_DIMENSIONS);
            dimensionKeys.push(keys);
            dimensionProperties = Object.assign(Object.assign({}, dimensionProperties), d);
        });
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const createBody = () => {
            return Object.assign(Object.assign(Object.assign({}, dimensionProperties), context.properties), { _aws: Object.assign(Object.assign({}, context.meta), { CloudWatchMetrics: [
                        {
                            Dimensions: dimensionKeys,
                            Metrics: [],
                            Namespace: context.namespace,
                        },
                    ] }) });
        };
        const eventBatches = [];
        let currentBody = createBody();
        const currentMetricsInBody = () => currentBody._aws.CloudWatchMetrics[0].Metrics.length;
        const shouldSerialize = () => currentMetricsInBody() === Constants_1.Constants.MAX_METRICS_PER_EVENT;
        // converts the body to JSON and pushes it into the batches
        const serializeCurrentBody = () => {
            eventBatches.push(JSON.stringify(currentBody));
            currentBody = createBody();
        };
        for (const [key, metric] of context.metrics) {
            // if there is only one metric value, unwrap it to make querying easier
            const metricValue = metric.values.length === 1 ? metric.values[0] : metric.values;
            currentBody[key] = metricValue;
            currentBody._aws.CloudWatchMetrics[0].Metrics.push({ Name: key, Unit: metric.unit });
            if (shouldSerialize()) {
                serializeCurrentBody();
            }
        }
        if (eventBatches.length === 0 || currentMetricsInBody() > 0) {
            serializeCurrentBody();
        }
        return eventBatches;
    }
}
exports.LogSerializer = LogSerializer;
