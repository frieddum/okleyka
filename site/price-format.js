/* The scales are explained on the methodology page. */
(() => {
  function formatPrice(band, lang) {
    if (!band || !Number.isInteger(band.level) || band.level < 1 || band.level > 5) return null;
    const basis = band.estimated_for_ml
      ? (lang === 'en' ? ` · ≈ ${band.estimated_for_ml} ml` : ` · ≈ ${band.estimated_for_ml} мл`)
      : band.gift_set ? (lang === 'en' ? ' · gift set' : ' · набор') : '';
    const size = basis || (band.volume_ml < 330 || (band.scale === 'wine' && band.volume_ml === 375)
      ? (lang === 'en' ? ` · ${band.volume_ml} ml` : ` · ${band.volume_ml} мл`) : '');
    const approximate = band.market_estimate && !band.estimated_for_ml;
    return {symbols: (approximate ? '≈ ' : '') + '$'.repeat(band.level) + size,
      label: (approximate ? (lang === 'en' ? 'Estimated ' : 'Ориентировочный ') : '') +
        (lang === 'en' ? `Price level ${band.level} of 5` : `Ценовой уровень ${band.level} из 5`) + size};
  }
  if (typeof module !== 'undefined') module.exports = formatPrice;
  else window.formatPriceBand = formatPrice;
})();
