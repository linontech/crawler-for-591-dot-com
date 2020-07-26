<template>
  <select v-model="selectedIndex">
    <option v-for="(item, index) in dataSource" :value="index" :key="index">
      {{ item }}
    </option>
  </select>
</template>

<script>

let selectedIndex = {
  get: function () {
    return this.value
  },
  set: function (val) {
    this.$emit('input', val)
  }
}

export default {
  name: 'customized-select',
  props: [
    'value',
    'dataSource'
  ],
  computed: {
    selectedIndex
  }
}
</script>
