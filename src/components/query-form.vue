<template>
  <div class='query-form'>
      <h3>{{ msg }}</h3>
      <button type='button' class='start_button' href='/start'>Start</button>
      <button type='button' class='stop_button' href='/stop'>Stop</button>
      <pre class='crawl_status'>Crawl Status: </pre>

    <form class='search' method='POST' action='/search' @submit.prevent="submitForm($data)">
      <div class="form-group">
        <label for="townIndex">Town</label>
        <customized-select type="text" id="townIndex" name="townIndex" v-model="townIndex" :data-source="towns"/>
        <label for="areaid">Area</label>
        <customized-select type="text" id="areaid" name="areaid" v-model="areaIndex" :data-source="areas"/>
      </div>
<!--      {{ zip }}-->
      <div class="form-footer">
        <button type="submit" name="submit" class="btn">Submit</button>
      </div>
    </form>
<!--      <ul>-->
<!--        <li> {{ form.regionid.label }} {{ form.regionid }} </li><br/>-->
<!--        <li> {{ form.price_upper.label }} {{ form.price_upper }}-->
<!--             {{ form.price_lower.label }} {{ form.price_lower }} </li><br/>-->
<!--        <li> {{ form.area_upper.label }} {{ form.area_upper }}-->
<!--             {{ form.area_lower.label }} {{ form.area_lower }} </li><br/>-->
<!--        <li> {{ form.lessor_sex.label }} {{ form.lessor_sex }} </li><br/>-->
<!--        <li> {{ form.role_type.label }} {{ form.role_type }} </li><br/>-->
<!--        <li> {{ form.linkman.label }} {{ form.linkman }}</li><br/>-->
<!--        <li> {{ form.tel.label }} {{ form.tel }}</li><br/>-->
<!--        <li> {{ form.sex.label }} {{ form.sex }} </li><br/>-->
<!--      </ul>-->
<!--      {{ form.submit }}-->
    <pre>Show only first 100 data.</pre>
    <pre class='search_response'></pre>
    <pre class='json_data'></pre>
  </div>
</template>

<script>
import $ from 'jquery'
import CustomizedSelect from './customized-select'
import $backend from '../backend'
import Cities from './const-plugin'

export default {
  name: 'query-form',
  components: { CustomizedSelect },
  props: {
    msg: String
  },
  data () {
    return {
      townIndex: 0, // townIndex
      areaIndex: 0
    }
  },
  computed: {
    towns: function () {
      return Cities.map(x => x.name)
    },
    areas: function () {
      return Cities[this.townIndex].areas.map(x => x.name)
    },
    zip: function () {
      return Cities[this.townIndex].areas[this.areaIndex].zip
    },
    regionid: function () {
      return Cities[this.townIndex].regionid
    } // TODO: how to dynamic get regionid
  },
  watch: {
    townIndex: function () {
      this.areaIndex = 0
    }
  },
  created () {
  },
  methods: {
    startCrawling: function () {
      $('.crawl_status').text('Status: sending request.')
      $backend.startCrawling().then(
        response => {
          console.log(response.message)
          $('.crawl_status').text('Status: ' + response.message)
        }).catch(error => {
        console.log('start error')
        $('.crawl_status').text('Status: app encounter error.\n' + error.message)
      })
    },
    stopCrawling: function () {
      $('.crawl_status').text('Status: sending request.')
      $backend.stopCrawling().then(
        response => {
          console.log(response.message)
          $('.crawl_status').text('Status: ' + response.message)
        }).catch(error => {
        console.log('stop error')
        $('.crawl_status').text('Status: app encounter error when stopping.\n' + error.message)
      })
    },
    submitForm: function (payload) {
      $backend.queryRecords(JSON.stringify(payload)).then(response => {
        $('.json_data').text(response.data)
        $('.search_response').text(response.message)
        console.log(response.message)
      }).catch(error => {
        $('.search_response').text('search encounter error.\n' + error.message)
        console.log('search encounter error.')
      })
      return false
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
