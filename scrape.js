const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

const cities = [
 "istanbul",
 "ankara",
 "izmir",
 "adana",
 "antalya"
 // 81 ili buraya ekle
];

async function scrapeCity(city) {
  try {
    const url = `https://benzinal.com/${city}-benzin-fiyatlari`;
    const { data } = await axios.get(url);
    const $ = cheerio.load(data);

    let stations = [];

    $("table tbody tr").each((i, el) => {
      const brand = $(el).find("td").eq(0).text().trim();
      const benzin = $(el).find("td").eq(1).text().trim();
      const motorin = $(el).find("td").eq(2).text().trim();
      const lpg = $(el).find("td").eq(3).text().trim();

      if (brand) {
        stations.push({ brand, benzin, motorin, lpg });
      }
    });

    return stations;

  } catch (err) {
    console.log(city + " hata verdi");
    return [];
  }
}

async function scrapeAll() {
  let allData = {};

  for (let city of cities) {
    console.log(city + " çekiliyor...");
    const data = await scrapeCity(city);
    allData[city] = data;
  }

  fs.writeFileSync("fuel-data.json", JSON.stringify(allData, null, 2));
  console.log("fuel-data.json oluşturuldu.");
}

scrapeAll();