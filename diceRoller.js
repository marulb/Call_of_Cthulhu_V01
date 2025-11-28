/* ============================================================================
   CoC Dice Roller - Reusable Dice Rolling System
   ============================================================================ */

/**
 * Roll standard dice expression like "1D6+2D4-2"
 * @param {string} expression - Dice expression (e.g., "3D6", "2D10+1D4-3")
 * @returns {object} - Result object with total and details
 */
function rollDiceExpression(expression) {
  const cleanExpression = expression.toUpperCase().replace(/\s+/g, '');
  const diceRegex = /(\d+)D(\d+)/g;
  const modRegex = /([+-](?!\d*D)\d+)/g;
  
  let total = 0;
  let modTotal = 0;
  let output = [];
  
  // Roll all dice
  let diceMatch;
  while ((diceMatch = diceRegex.exec(cleanExpression)) !== null) {
    const num = parseInt(diceMatch[1]);
    const sides = parseInt(diceMatch[2]);
    let diceRolls = [];
    let diceTotal = 0;
    
    for (let i = 0; i < num; i++) {
      const roll = Math.floor(Math.random() * sides) + 1;
      diceRolls.push(roll);
      diceTotal += roll;
    }
    
    total += diceTotal;
    output.push({
      type: `${num}D${sides}`,
      rolls: diceRolls,
      subtotal: diceTotal
    });
  }
  
  // Apply modifiers
  let modMatch;
  while ((modMatch = modRegex.exec(cleanExpression)) !== null) {
    const mod = parseInt(modMatch[1]);
    modTotal += mod;
  }
  
  total += modTotal;
  
  return {
    total: total,
    rolls: output,
    modifier: modTotal,
    expression: expression
  };
}

/**
 * Roll percentage dice (D100) with bonus/penalty dice
 * @param {number} numBonus - Number of bonus dice
 * @param {number} numPenalty - Number of penalty dice
 * @returns {object} - Result object with final result and all rolls
 */
function rollPercentDice(numBonus = 0, numPenalty = 0) {
  const tens = Math.floor(Math.random() * 10) * 10;
  const units = Math.floor(Math.random() * 10);
  const diff = numBonus - numPenalty;
  
  let effectiveBonus = 0;
  let effectivePenalty = 0;
  let bonusRolls = [];
  let penaltyRolls = [];
  
  if (diff > 0) {
    effectiveBonus = diff;
    for (let i = 0; i < effectiveBonus; i++) {
      bonusRolls.push(Math.floor(Math.random() * 10) * 10);
    }
  } else if (diff < 0) {
    effectivePenalty = -diff;
    for (let i = 0; i < effectivePenalty; i++) {
      penaltyRolls.push(Math.floor(Math.random() * 10) * 10);
    }
  }
  
  let finalTens = tens;
  if (effectiveBonus > 0) {
    finalTens = Math.min(tens, ...bonusRolls);
  } else if (effectivePenalty > 0) {
    finalTens = Math.max(tens, ...penaltyRolls);
  }
  
  const result = finalTens + units;
  const displayResult = result === 0 ? 100 : result;
  
  return {
    result: displayResult,
    tens: tens,
    units: units,
    bonusRolls: bonusRolls,
    penaltyRolls: penaltyRolls,
    effectiveBonus: effectiveBonus,
    effectivePenalty: effectivePenalty
  };
}

/**
 * Format dice roll result for display
 * @param {object} result - Result from rollDiceExpression()
 * @returns {string} - Formatted HTML string
 */
function formatDiceResult(result) {
  let output = [];
  
  result.rolls.forEach(roll => {
    output.push(`${roll.type}: ${roll.rolls.join(', ')} (${roll.subtotal})`);
  });
  
  if (result.modifier !== 0) {
    output.push(`Mod: ${result.modifier}`);
  }
  
  return `
    <p>${output.join('<br>')}</p>
    <p><strong>Result:</strong> ${result.total}</p>
  `;
}

/**
 * Format percentage dice result for display
 * @param {object} result - Result from rollPercentDice()
 * @returns {string} - Formatted HTML string
 */
function formatPercentResult(result) {
  return `
    <p><strong>Tens:</strong> ${result.tens}</p>
    <p><strong>Units:</strong> ${result.units}</p>
    ${result.effectiveBonus > 0 ? `<p><strong>Bonus:</strong> ${result.bonusRolls.join(', ')}</p>` : ''}
    ${result.effectivePenalty > 0 ? `<p><strong>Penalty:</strong> ${result.penaltyRolls.join(', ')}</p>` : ''}
    <p><strong>Result:</strong> ${result.result}%</p>
  `;
}
