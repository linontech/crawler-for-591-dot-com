<template>
  <div class="home">
    <QueryForm msg="Welcome to House Renting Go"/>
  </div>
</template>

<script>
// @ is an alias to /src
import QueryForm from '../components/query-form.vue'

export default {
  name: 'home',
  props: {
  },
  components: {
    QueryForm
  }
}
</script>

<style lang="scss">

</style>
