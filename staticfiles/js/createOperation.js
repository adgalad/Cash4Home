
const optionsBackup = {}

var currentInput = 0
var nOptions = 5

function addAccountInput () {
  if (currentInput < 4) {
    ++currentInput
    $('#id_form-' + currentInput + '-amount').parent().show()
    $('#id_form-' + currentInput + '-account').parent().show()
  }
  if (currentInput == 4) {
    $('#add').prop('disabled', true)
  }
  if (currentInput > 0) {
    $('#delete').prop('disabled', false)
  }
}

function deleteAccountInput () {
  if (currentInput > 0) {
    $('#id_form-' + currentInput + '-amount').val(0.0).parent().hide()
    $('#id_form-' + currentInput + '-account').val('').parent().hide()
    --currentInput
    summary()
  }
  if (currentInput == 0) {
    $('#delete').prop('disabled', true)
  }
  if (currentInput < 4) {
    $('#add').prop('disabled', false)
  }
}

summary = function () {
  var total = 0
  for (var i = 0; i < nOptions; ++i) {
    var field = $('#id_form-' + i + '-amount')
    if (field.parent().is(':visible')) {
      var v = parseInt(field.val())
      total += isNaN(v) ? 0 : v
    }
  }
  toCurrency = $('#id_currency').val()
  if (parseInt($('#id_account').val())) {
    fromCurrency = fromAccs[parseInt($('#id_account').val())]['currency']
    _rate = rate[fromCurrency + '/' + toCurrency]
    _fee = String(fee * 100) + '%'
    amount = fromCurrency + ' ' + String(total)
    net = fromCurrency + ' ' + String(total * (1 - fee))
    __rate = String(_rate) + ' ' + fromCurrency + '/' + toCurrency
    vef = toCurrency + ' ' + String(total * (1 - fee) * 800000)
    amountIn = 'Total en ' + toCurrency

    $('#fee').html(_fee)
    $('#amount').html(amount)
    $('#net').html(net)
    $('#rate').html(__rate)
    $('#vef').html(vef)
    $('#amountIn').html(amountIn)

    $('#fee2').html(_fee)
    $('#amount2').html(amount)
    $('#net2').html(net)
    $('#rate2').html(__rate)
    $('#vef2').html(vef)
    $('#amountIn2').html(amountIn)

    $('#td-from').html(fromAccs[parseInt($('#id_account').val())]['name'])

    table = $('#toAccTable')
    table.html('')
    for (var i = 0; i < nOptions - 1; ++i) {
      var acc = toAccs[$('#id_form-' + i + '-account').val()]
      var amount = parseInt($('#id_form-' + i + '-amount').val()) * _rate
      if (!acc) continue
      table.append(`
                  <tr>
                    <td><b>Cuenta ` + String(i + 1) + `</b></td>
                    <td>` + acc['name'] + `</td>
                    <td>` + acc['currency'] + ' ' + String(amount) + `</td>
                  </tr>`)
    }
  }
}

selectAccount = function () {
  $('option').prop('disabled', false)
  for (var i = 0; i <= currentInput; ++i) {
    var value = String($('#id_form-' + i + '-account').val())
    if (value != '') {
      var options = $('option[value="' + value + '"]')
      $('option[value="' + value + '"]').filter(item => {
        return $('#' + options[item].parentNode.id).val() != value
      }).prop('disabled', true)
    }
  }
}

changeCurrency = function () {
  for (var i = 0; i < nOptions; ++i) {
    input = $('#id_form-' + i + '-account')
    input.html('')
    for (var j in optionsBackup) {
      input.append(optionsBackup[i][j])
    }
  }
  for (var key in toAccs) {
    if (toAccs[parseInt(key)]['currency'] != $('#id_currency').val()) {
      $('option[value="' + key + '"]').remove()
    }
  }
  summary()
}

for (var i = 0; i < nOptions; ++i) {
  $('#id_currency').change(changeCurrency)
  $('#id_account').change(summary)

  $('#id_form-' + i + '-account').change(selectAccount)

  var field = $('#id_form-' + i + '-amount')

  field.keyup(summary).change(summary).val(0.0)
  if (i > 0) {
    field.parent().hide()
    $('#id_form-' + i + '-account').parent().hide()
  }

  optionsBackup[i] = $('#id_form-' + i + '-account').children()

  summary()
}
