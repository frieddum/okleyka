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
    const brandPrefix = /^(?:Wine People|White Horse|White Oak|Port Charlotte|Port Askaig)\b/i;
    if (!brandPrefix.test(rest)) {
      const ruAdj = '(?:белое|красное|розовое|оранжевое|игристое|сухое|полусухое|сладкое|полусладкое|сладкая|горькая|полусладкая|серебряная|светлое|т[её]мное|пшеничное|нефильтрованное|фильтрованное|непастеризованное|пастеризованное|неосветленное|безалкогольное|крепл[её]ное|десертный|десертное|спиртной|ароматизированный|пивной|органическое|виноградное|виноградосодержащий|купажированный|односолодовый|солодовый|сортовое|выдержанное|выдержанный|газированный|алкогольный|винный)';
      const adjective = '(?:' + ruAdj + '|silver|organic|flavoured|flavored|spirit|light|filtered|unfiltered|pasteurized|unpasteurized|non-alcoholic|alcohol-free|wheat|blended|single malt|white|red|ros[eé]|orange|sparkling|dry|semi-dry|sweet|semi-sweet|dessert|fortified|aged)';
      const kind = '(?:шампанское|champagne|просекко|prosecco|портвейн|port|херес|sherry|кальвадос|calvados|креман|cremant|соджу|soju|писко|pisco|аперитив|aperitif|винодельня|winery|вино|виски|лик[её]р|ром|водка|джин|коньяк|бренди|текила|вермут|пиво|сидр|сакэ|настойка|бальзам|напиток|wine|whisk[ey]+|liqueur|rum|vodka|gin|cognac|brandy|tequila|vermouth|beer|cider|sake|tincture)';
      const prefix = new RegExp('^(?:' + adjective + '\\s+)*' + kind + '(?:\\s+' + adjective + ')*\\s+', 'iu');
      let match;
      while (!brandPrefix.test(rest) && (match = rest.match(prefix))) {
        // Do not consume the first word of a protected brand after the type.
        const brand = match[0].match(/\b(White)\s*$/i);
        let length = match[0].length;
        if (brand && /^(?:Horse|Oak)\b/i.test(rest.slice(length))) length = match[0].lastIndexOf(brand[1]);
        parts.push(rest.slice(0, length).trim()); rest = rest.slice(length);
      }
      // Some retailer names have already lost their type, leaving an adjective first.
      const descriptors = rest.match(new RegExp('^(?:(?!золотая\\s)' + ruAdj + '\\s+)+', 'iu'));
      if (descriptors) { parts.push(descriptors[0].trim()); rest = rest.slice(descriptors[0].length); }
    }
    const metadata = rest.match(/^(?:Подробнее о|More about|Спирт (?:Альфа|Люкс)|(?:Alpha|Lux) alcohol|стиль №?\s*\d+)\s+/iu);
    if (metadata) { parts.push(metadata[0].trim()); rest = rest.slice(metadata[0].length); }
    return rest ? {title: rest, details: parts.join(' · ')} : {title: clean || original, details: ''};
  }
  splitName.withoutQuotes = withoutQuotes;
  splitName.beerTags = function (name, category) {
    if (category !== 'Пиво') return [];
    let s = name.toLowerCase().replace(/ё/g, 'е');
    // Reviewed retailer error: Hofbrau Original is not a wheat beer.
    if (/hofbr[aä]u original/i.test(s)) s = s.replace(/пшенич\S*|\bwheat\b/g, '');
    return [
      ['Светлое', /светлое|\b(?:blond|blonde|helles|pale)\b/],
      ['Тёмное', /темное|\b(?:dark|dunkel|schwarzbier)\b/],
      ['Пшеничное', /пшенич|\b(?:wheat|weizen|weissbier|weizenbier|witbier|hefeweizen)\b/],
      ['Лагер', /лагер|\b(?:lager|pilsner|pilsener|pils|helles)\b/],
      ['Эль', /(?:^|\s)эль(?:\s|$)|\b(?:ale|ipa)\b/],
      ['IPA', /\bipa\b|ипа(?:\s|$)/],
      ['Стаут', /стаут|\bstout\b/],
      ['Портер', /портер|\bporter\b/],
      ['Безалкогольное', /безалкогольн|\b(?:non-alcoholic|alcohol-free)\b/]
    ].filter(([, re]) => re.test(s)).map(([tag]) => tag);
  };
  if (typeof module !== 'undefined') module.exports = splitName;
  else window.splitDrinkName = splitName;
})();
