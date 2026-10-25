/* The scales are explained on the methodology page. */
(() => {
  function formatPrice(band, lang) {
    if (!band || !Number.isInteger(band.level) || band.level < 1 || band.level > 5) return null;
    return {symbols: '$'.repeat(band.level),
      label: lang === 'en' ? `Price level ${band.level} of 5` : `Ценовой уровень ${band.level} из 5`};
  }
  if (typeof module !== 'undefined') module.exports = formatPrice;
  else window.formatPriceBand = formatPrice;
})();
