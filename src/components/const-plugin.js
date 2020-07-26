
// TODO: get id mappings from 591, save it at backend and load into vue. Use backups if not loaded.
const Cities = [
  {
    name: '台北市',
    regionid: 0,
    areas: [
      { name: '中正區', sectionid: 3, zip: '300' },
      { name: '大安區', sectionid: 5, zip: '304' },
      { name: '信義區', sectionid: 7, zip: '306' },
      { name: '士林區', sectionid: 8, zip: '307' },
      { name: '內湖區', sectionid: 10, zip: '309' },
      { name: '中山區', sectionid: 1, zip: '302' },
      { name: '松山區', sectionid: 4, zip: '303' },
      { name: '大同區', sectionid: 2, zip: '301' },
      { name: '萬華區', sectionid: 6, zip: '305' },
      { name: '文山區', sectionid: 12, zip: '311' },
      { name: '北投區', sectionid: 9, zip: '308' },
      { name: '南港區', sectionid: 11, zip: '310' }
    ]
  },
  {
    name: '新北市',
    regionid: 2,
    areas: [
      { name: '新竹市', zip: '400' }
    ]
  }
]

// Cities.install = function (Vue) {
//     Vue.prototype.$getConst = (key) => {
//         return Cities[key];
//     }
// };

export default Cities
