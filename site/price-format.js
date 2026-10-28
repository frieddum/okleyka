/* The scales are explained on the methodology page. */
(() => {
  function formatPrice(band, lang) {
    if (!band || !Number.isInteger(band.level) || band.level < 1 || band.level > 5) return null;
    const size = band.scale === 'wine' && band.volume_ml === 375
      ? (lang === 'en' ? ' · 375 ml' : ' · 375 мл') : '';
    return {symbols: '$'.repeat(band.level) + size,
      label: (lang === 'en' ? `Price level ${band.level} of 5` : `Ценовой уровень ${band.level} из 5`) + size};
  }
  if (typeof module !== 'undefined') module.exports = formatPrice;
  else window.formatPriceBand = formatPrice;
})();
