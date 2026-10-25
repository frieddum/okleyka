/* Display-only: retain the original name for identity and searching. */
(() => {
  function withoutQuotes(name) {
    return name.replace(/["«»„“”‟]/gu, '')
      // Paired single quotation marks; apostrophes inside names stay intact.
      .replace(/(^|[\s(])['‘]([^'‘’]+)['’](?=$|[\s,.;:)])/gu, '$1$2')
      .replace(/^['‘’]+(?=\p{L})/u, '');
  }
  function splitName(original) {
    const clean = withoutQuotes(original).trim();
    let rest = clean, parts = [];
    const volume = rest.match(/^\d+(?:[.,]\d+)?\s*(?:мл|ml|л|l)(?=\s|$)\s*/iu);
    if (volume) { parts.push(volume[0].trim()); rest = rest.slice(volume[0].length); }
    // These are names, not product-type prefixes.
    if (!/^(?:Wine People|White Horse|White Oak|Port Charlotte|Port Askaig)\b/i.test(rest)) {
      const adjective = '(?:белое|красное|розовое|оранжевое|игристое|сухое|полусухое|сладкое|полусладкое|крепл[её]ное|десертный|десертное|виноградное|сортовое|выдержанное|выдержанный|газированный|алкогольный|винный|white|red|ros[eé]|orange|sparkling|dry|semi-dry|sweet|semi-sweet|dessert|fortified|aged)';
      const kind = '(?:вино|виски|лик[её]р|ром|водка|джин|коньяк|бренди|текила|вермут|пиво|сидр|сакэ|напиток|wine|whisk[ey]+|liqueur|rum|vodka|gin|cognac|brandy|tequila|vermouth|beer|cider|sake)';
      const prefix = new RegExp('^(?:' + adjective + '\\s+)*' + kind + '(?:\\s+' + adjective + ')*\\s+', 'iu');
      const match = rest.match(prefix);
      if (match) { parts.push(match[0].trim()); rest = rest.slice(match[0].length); }
    }
    return rest ? {title: rest, details: parts.join(' · ')} : {title: clean || original, details: ''};
  }
  splitName.withoutQuotes = withoutQuotes;
  if (typeof module !== 'undefined') module.exports = splitName;
  else window.splitDrinkName = splitName;
})();
