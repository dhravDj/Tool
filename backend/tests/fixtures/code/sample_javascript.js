/**
 * Sample JavaScript module for code intelligence testing.
 */
const fs = require('fs');
const path = require('path');
const lodash = require('lodash');

class CalculationService {
    constructor(baseMultiplier = 1) {
        this.baseMultiplier = baseMultiplier;
    }

    calculateTotal(items) {
        debugger; // test diagnostic detection
        return items.reduce((sum, item) => sum + (item.price * this.baseMultiplier), 0);
    }
}

function processBatch(batchId) {
    console.log("Processing batch: " + batchId);
    return true;
}

module.exports = { CalculationService, processBatch };
