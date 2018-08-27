/*
 * SmartWizard 3.3.1 plugin
 * jQuery Wizard control Plugin
 * by Dipu
 *
 * Refactored and extended:
 * https://github.com/mstratman/jQuery-Smart-Wizard
 *
 * Original URLs:
 * http://www.techlaboratory.net
 * http://tech-laboratory.blogspot.com
 */

function SmartWizard (target, options) {
  this.target = target
  this.options = options
  this.curStepIdx = options.selected
  this.steps = $(target).children('ul').children('li').children('a') // Get all anchors
  this.contentWidth = 0
  this.msgBox = $('<div class="msgBox"><div class="content"></div><a href="#" class="close">X</a></div>')
  this.elmStepContainer = $('<div></div>').addClass('stepContainer')
  this.loader = $('<div>Loading</div>').addClass('loader')
  this.buttons = {
    next: $('<button class="btn btn-primary" type="button">' + options.labelNext + '</button>').addClass('buttonNext'),
    previous: $('<button class="btn btn-primary" type="button">' + options.labelPrevious + '</button>').addClass('buttonPrevious'),
    finish: $('<button class="btn submit" type="submit">' + options.labelFinish + '</button>').addClass('buttonFinish')
  }

    /*
     * Private functions
     */

  var _init = function ($this) {
    var elmActionBar = $('<div></div>').addClass('actionBar')
    elmActionBar.append($this.msgBox)
    $('.close', $this.msgBox).click(function () {
      $this.msgBox.fadeOut('normal')
      return false
    })

    var allDivs = $this.target.children('div')
    $this.target.children('ul').addClass('anchor')
    allDivs.addClass('content')

        // highlight steps with errors
    if ($this.options.errorSteps && $this.options.errorSteps.length > 0) {
      $.each($this.options.errorSteps, function (i, n) {
        $this.setError({ stepnum: n, iserror: true })
      })
    }

    $this.elmStepContainer.append(allDivs)
    elmActionBar.append($this.loader)
    $this.target.append($this.elmStepContainer)
    elmActionBar.append($this.buttons.previous)
                .append($this.buttons.next)
                .append($this.buttons.finish)
    $this.target.append(elmActionBar)
    this.contentWidth = $this.elmStepContainer.width()

    $($this.buttons.next).click(function () {
      $this.goForward()
      return false
    })
    $($this.buttons.previous).click(function () {
      $this.goBackward()
      return false
    })
    $($this.buttons.finish).click(function () {
      if (!$(this).hasClass('buttonDisabled')) {
        if ($.isFunction($this.options.onFinish)) {
          var context = { fromStep: $this.curStepIdx + 1 }
          if (!$this.options.onFinish.call(this, $($this.steps), context)) {
            return false
          }
        } else {
          var frm = $this.target.parents('form')
          if (frm && frm.length) {
            frm.submit()
          }
        }
      }
      return false
    })

    $($this.steps).bind('click', function (e) {
      if ($this.steps.index(this) == $this.curStepIdx) {
        return false
      }
      var nextStepIdx = $this.steps.index(this)
      var isDone = $this.steps.eq(nextStepIdx).attr('isDone') - 0
      if (isDone == 1) {
        _loadContent($this, nextStepIdx)
      }
      return false
    })

        // Enable keyboard navigation
    if ($this.options.keyNavigation) {
      $(document).keyup(function (e) {
        if (e.which == 39) { // Right Arrow
          $this.goForward()
        } else if (e.which == 37) { // Left Arrow
          $this.goBackward()
        }
      })
    }
        //  Prepare the steps
    _prepareSteps($this)
        // Show the first slected step
    _loadContent($this, $this.curStepIdx)
  }

  var _prepareSteps = function ($this) {
    if (!$this.options.enableAllSteps) {
      $($this.steps, $this.target).removeClass('selected').removeClass('done').addClass('disabled')
      $($this.steps, $this.target).attr('isDone', 0)
    } else {
      $($this.steps, $this.target).removeClass('selected').removeClass('disabled').addClass('done')
      $($this.steps, $this.target).attr('isDone', 1)
    }

    $($this.steps, $this.target).each(function (i) {
      $($(this).attr('href').replace(/^.+#/, '#'), $this.target).hide()
      $(this).attr('rel', i + 1)
    })
  }

  var _step = function ($this, selStep) {
    return $(
            $(selStep, $this.target).attr('href').replace(/^.+#/, '#'),
            $this.target
        )
  }

  var _loadContent = function ($this, stepIdx) {
    var selStep = $this.steps.eq(stepIdx)
    var ajaxurl = $this.options.contentURL
    var ajaxurl_data = $this.options.contentURLData
    var hasContent = selStep.data('hasContent')
    var stepNum = stepIdx + 1
    if (ajaxurl && ajaxurl.length > 0) {
      if ($this.options.contentCache && hasContent) {
        _showStep($this, stepIdx)
      } else {
        var ajax_args = {
          url: ajaxurl,
          type: 'POST',
          data: ({step_number: stepNum}),
          dataType: 'text',
          beforeSend: function () {
            $this.loader.show()
          },
          error: function () {
            $this.loader.hide()
          },
          success: function (res) {
            $this.loader.hide()
            if (res && res.length > 0) {
              selStep.data('hasContent', true)
              _step($this, selStep).html(res)
              _showStep($this, stepIdx)
            }
          }
        }
        if (ajaxurl_data) {
          ajax_args = $.extend(ajax_args, ajaxurl_data(stepNum))
        }
        $.ajax(ajax_args)
      }
    } else {
      _showStep($this, stepIdx)
    }
  }

  var _showStep = function ($this, stepIdx) {
    var selStep = $this.steps.eq(stepIdx)
    var curStep = $this.steps.eq($this.curStepIdx)
    if (stepIdx != $this.curStepIdx) {
      if ($.isFunction($this.options.onLeaveStep)) {
        var context = { fromStep: $this.curStepIdx + 1, toStep: stepIdx + 1 }
        if (!$this.options.onLeaveStep.call($this, $(curStep), context)) {
          return false
        }
      }
    }
    $this.elmStepContainer.height(_step($this, selStep).outerHeight())
    var prevCurStepIdx = $this.curStepIdx
    $this.curStepIdx = stepIdx
    if ($this.options.transitionEffect == 'slide') {
      _step($this, curStep).slideUp('fast', function (e) {
        _step($this, selStep).slideDown('fast')
        _setupStep($this, curStep, selStep)
      })
    } else if ($this.options.transitionEffect == 'fade') {
      _step($this, curStep).fadeOut('fast', function (e) {
        _step($this, selStep).fadeIn('fast')
        _setupStep($this, curStep, selStep)
      })
    } else if ($this.options.transitionEffect == 'slideleft') {
      var nextElmLeft = 0
      var nextElmLeft1 = null
      var nextElmLeft = null
      var curElementLeft = 0
      if (stepIdx > prevCurStepIdx) {
        nextElmLeft1 = $this.contentWidth + 10
        nextElmLeft2 = 0
        curElementLeft = 0 - _step($this, curStep).outerWidth()
      } else {
        nextElmLeft1 = 0 - _step($this, selStep).outerWidth() + 20
        nextElmLeft2 = 0
        curElementLeft = 10 + _step($this, curStep).outerWidth()
      }
      if (stepIdx == prevCurStepIdx) {
        nextElmLeft1 = $($(selStep, $this.target).attr('href'), $this.target).outerWidth() + 20
        nextElmLeft2 = 0
        curElementLeft = 0 - $($(curStep, $this.target).attr('href'), $this.target).outerWidth()
      } else {
        $($(curStep, $this.target).attr('href'), $this.target).animate({left: curElementLeft}, 'fast', function (e) {
          $($(curStep, $this.target).attr('href'), $this.target).hide()
        })
      }

      _step($this, selStep).css('left', nextElmLeft1).show().animate({left: nextElmLeft2}, 'fast', function (e) {
        _setupStep($this, curStep, selStep)
      })
    } else {
      _step($this, curStep).hide()
      _step($this, selStep).show()
      _setupStep($this, curStep, selStep)
    }
    return true
  }

  var _setupStep = function ($this, curStep, selStep) {
    $(curStep, $this.target).removeClass('selected')
    $(curStep, $this.target).addClass('done')

    $(selStep, $this.target).removeClass('disabled')
    $(selStep, $this.target).removeClass('done')
    $(selStep, $this.target).addClass('selected')

    $(selStep, $this.target).attr('isDone', 1)

    _adjustButton($this)

    if ($.isFunction($this.options.onShowStep)) {
      var context = { fromStep: parseInt($(curStep).attr('rel')), toStep: parseInt($(selStep).attr('rel')) }
      if (!$this.options.onShowStep.call(this, $(selStep), context)) {
        return false
      }
    }
    if ($this.options.noForwardJumping) {
            // +2 == +1 (for index to step num) +1 (for next step)
      for (var i = $this.curStepIdx + 2; i <= $this.steps.length; i++) {
        $this.disableStep(i)
      }
    }
  }

  var _adjustButton = function ($this) {
    if (!$this.options.cycleSteps) {
      if ($this.curStepIdx <= 0) {
        $($this.buttons.previous).addClass('buttonDisabled')
        if ($this.options.hideButtonsOnDisabled) {
          $($this.buttons.previous).hide()
        }
      } else {
        $($this.buttons.previous).removeClass('buttonDisabled')
        if ($this.options.hideButtonsOnDisabled) {
          $($this.buttons.previous).show()
        }
      }
      if (($this.steps.length - 1) <= $this.curStepIdx) {
        $($this.buttons.next).addClass('buttonDisabled')
        if ($this.options.hideButtonsOnDisabled) {
          $($this.buttons.next).hide()
        }
      } else {
        $($this.buttons.next).removeClass('buttonDisabled')
        if ($this.options.hideButtonsOnDisabled) {
          $($this.buttons.next).show()
        }
      }
    }
        // Finish Button
    if ($this.curStepIdx == 2 && (!$this.steps.hasClass('disabled') || $this.options.enableFinishButton)) {
      $($this.buttons.finish).removeClass('buttonDisabled')
      if ($this.options.hideButtonsOnDisabled) {
        $($this.buttons.finish).show()
      }
    } else {
      $($this.buttons.finish).addClass('buttonDisabled')
      if ($this.options.hideButtonsOnDisabled) {
        $($this.buttons.finish).hide()
      }
    }
  }

    /*
     * Public methods
     */

  SmartWizard.prototype.goForward = function () {
    summary()
    $('.bad').removeClass('bad')
    if (this.curStepIdx == 0) {
      if (!$('#id_account').val()){
        $('#id_account').parent().addClass('bad')
        return
      } else if (!$('#id_currency').val()){
        $('#id_currency').parent().addClass('bad')
        return
      }
      fromCurrency = fromAccs[parseInt($('#id_account').val())]['currency']
      toCurrency = $('#id_currency').val()
      _rate = rate[fromCurrency + '/' + toCurrency]
      if (!_rate){
        alert("No se pueden realizar operaciones de " + fromCurrency + " a " + toCurrency + "\nIntente mas tarde.");
        return
      }
      loadStep2()
      
    } else if (this.curStepIdx == 1) {
      for (var i = 0; i <= currentInput; ++i) {
        if (!$('#id_form-' + i + '-account').val()) {
          return $('#id_form-' + i + '-account').parent().addClass('bad')
        } 
        else if (parseInt($('#id_form-' + i + '-amount').val()) <= 0) {
          return $('#id_form-' + i + '-amount').parent().addClass('bad')
        }
      }
    }

    var nextStepIdx = this.curStepIdx + 1
    if (this.steps.length <= nextStepIdx) {
      if (!this.options.cycleSteps) {
        return false
      }
      nextStepIdx = 0
    }
    _loadContent(this, nextStepIdx)
  }

  SmartWizard.prototype.goBackward = function () {
    $('.bad').removeClass('bad')
    var nextStepIdx = this.curStepIdx - 1
    if (nextStepIdx < 0) {
      if (!this.options.cycleSteps) {
        return false
      }
      nextStepIdx = this.steps.length - 1
    }
    _loadContent(this, nextStepIdx)
  }

  SmartWizard.prototype.goToStep = function (stepNum) {
    var stepIdx = stepNum - 1
    if (stepIdx >= 0 && stepIdx < this.steps.length) {
      _loadContent(this, stepIdx)
    }
  }
  SmartWizard.prototype.enableStep = function (stepNum) {
    var stepIdx = stepNum - 1
    if (stepIdx == this.curStepIdx || stepIdx < 0 || stepIdx >= this.steps.length) {
      return false
    }
    var step = this.steps.eq(stepIdx)
    $(step, this.target).attr('isDone', 1)
    $(step, this.target).removeClass('disabled').removeClass('selected').addClass('done')
  }
  SmartWizard.prototype.disableStep = function (stepNum) {
    var stepIdx = stepNum - 1
    if (stepIdx == this.curStepIdx || stepIdx < 0 || stepIdx >= this.steps.length) {
      return false
    }
    var step = this.steps.eq(stepIdx)
    $(step, this.target).attr('isDone', 0)
    $(step, this.target).removeClass('done').removeClass('selected').addClass('disabled')
  }
  SmartWizard.prototype.currentStep = function () {
    return this.curStepIdx + 1
  }

  SmartWizard.prototype.showMessage = function (msg) {
    $('.content', this.msgBox).html(msg)
    this.msgBox.show()
  }
  SmartWizard.prototype.hideMessage = function () {
    this.msgBox.fadeOut('normal')
  }
  SmartWizard.prototype.showError = function (stepnum) {
    this.setError(stepnum, true)
  }
  SmartWizard.prototype.hideError = function (stepnum) {
    this.setError(stepnum, false)
  }
  SmartWizard.prototype.setError = function (stepnum, iserror) {
    if (typeof stepnum === 'object') {
      iserror = stepnum.iserror
      stepnum = stepnum.stepnum
    }

    if (iserror) {
      $(this.steps.eq(stepnum - 1), this.target).addClass('error')
    } else {
      $(this.steps.eq(stepnum - 1), this.target).removeClass('error')
    }
  }

  SmartWizard.prototype.fixHeight = function () {
    var height = 0

    var selStep = this.steps.eq(this.curStepIdx)
    var stepContainer = _step(this, selStep)
    stepContainer.children().each(function () {
      height += $(this).outerHeight()
    })

        // These values (5 and 20) are experimentally chosen.
    stepContainer.height(height + 5)
    this.elmStepContainer.height(height + 20)
  }

  _init(this)
};

(function ($) {
  $.fn.smartWizard = function (method) {
    var args = arguments
    var rv
    var allObjs = this.each(function () {
      var wiz = $(this).data('smartWizard')
      if (typeof method === 'object' || !method || !wiz) {
        var options = $.extend({}, $.fn.smartWizard.defaults, method || {})
        if (!wiz) {
          wiz = new SmartWizard($(this), options)
          $(this).data('smartWizard', wiz)
        }
      } else {
        if (typeof SmartWizard.prototype[method] === 'function') {
          rv = SmartWizard.prototype[method].apply(wiz, Array.prototype.slice.call(args, 1))
          return rv
        } else {
          $.error('Method ' + method + ' does not exist on jQuery.smartWizard')
        }
      }
    })
    if (rv === undefined) {
      return allObjs
    } else {
      return rv
    }
  }

// Default Properties and Events
  $.fn.smartWizard.defaults = {
    selected: 0,  // Selected Step, 0 = first step
    keyNavigation: false, // Enable/Disable key navigation(left and right keys are used if enabled)
    enableAllSteps: false,
    transitionEffect: 'fade', // Effect on navigation, none/fade/slide/slideleft
    contentURL: null, // content url, Enables Ajax content loading
    contentCache: true, // cache step contents, if false content is fetched always from ajax url
    cycleSteps: false, // cycle step navigation
    enableFinishButton: false, // make finish button enabled always
    hideButtonsOnDisabled: false, // when the previous/next/finish buttons are disabled, hide them instead?
    errorSteps: [],    // Array Steps with errors
    labelNext: 'Siguiente',
    labelPrevious: 'Anterior',
    labelFinish: 'Finalizar',
    noForwardJumping: false,
    onLeaveStep: null, // triggers when leaving a step
    onShowStep: null,  // triggers when showing a step
    onFinish: null  // triggers when Finish button is clicked
  }
})(jQuery)






const optionsBackup = {}

var currentInput = 0
var nOptions = 5

function addAccountInput () {
  if (currentInput < 4) {
    ++currentInput
    $('#id_form-' + currentInput + '-amount').val(0)
    $('#id_form-' + currentInput + '-account').val("")
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
currencyf = function(value){
  if (typeof(value) == 'string'){
    v = parseFloat(value.replace(/[^0-9\.-]+/g, ''))
  } else {
    v = parseFloat(value)  
  }
  if (isNaN(v)) return 0
  return v.toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,')
}

fcurrency = function(value){
  if (typeof(value) == 'string'){
    v = parseFloat(value.replace(/[^0-9\.-]+/g, ''))
  } else {
    v = parseFloat(value)  
  }
  if (isNaN(v)) return 0
  return v
}

toCurrencyf = function(field){
  for (var i = 0; i < nOptions; ++i) {
    f = $('#id_form-' + i + '-amount')
    f.val(currencyf(f.val()))
  }
}

summary = function () {
  var total = 0
  for (var i = 0; i < nOptions; ++i) {
    var field = $('#id_form-' + i + '-amount')
    if (field.parent().is(':visible')) {
      var v = fcurrency(field.val())
      total += isNaN(v) ? 0 : v
    }
  }
  toCurrency = $('#id_currency').val()
  if (parseInt($('#id_account').val())) {
    fromCurrency = fromAccs[parseInt($('#id_account').val())]['currency']
    _rate = rate[fromCurrency + '/' + toCurrency]
    _fee = String(fee * 100) + '%'
    amount = fromCurrency + ' ' + currencyf(total)
    net = fromCurrency + ' ' + currencyf(total * (1 - fee))
    __rate = currencyf(_rate) + ' ' + fromCurrency + '/' + toCurrency
    ves = toCurrency + ' ' + currencyf(total * (1 - fee) * _rate)
    amountIn = 'Total en ' + toCurrency

    $('#fee').html(_fee)
    $('#amount').html(amount)
    $('#net').html(net)
    $('#rate').html(__rate)
    $('#ves').html(ves)
    $('#amountIn').html(amountIn)

    $('#fee2').html(_fee)
    $('#amount2').html(amount)
    $('#net2').html(net)
    $('#rate2').html(__rate)
    $('#ves2').html(ves)
    $('#amountIn2').html(amountIn)

    $('#td-from').html(fromAccs[parseInt($('#id_account').val())]['name'])

    table = $('#toAccTable')
    table.html('')
    for (var i = 0; i < nOptions; ++i) {
      var acc = toAccs[$('#id_form-' + i + '-account').val()]
      var amount = fcurrency($('#id_form-' + i + '-amount').val())
      if (!acc) continue
      table.append(`
                  <tr>
                    <td><b>Cuenta ` + String(i + 1) + `</b></td>
                    <td>` + acc['name'] + `</td>
                    <td>` + fromCurrency + ' ' + currencyf(amount) + `<br>
                        (`+ acc['currency'] + ' ' + currencyf(amount * _rate) + `)
                    </td>
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
    len = optionsBackup[i].length
    for (var j =0 ; j < len ; j++) {
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

loadStep2 = function(){
  for (var i = 0; i < nOptions; ++i) {

    $('#id_form-' + i + '-account').change(selectAccount).val("")

    var field = $('#id_form-' + i + '-amount')
    field.attr('type', 'text')
    
    field.keyup(summary).change(summary).blur(toCurrencyf).val(0.0)
    if (i > 0) {
      field.parent().hide()
      $('#id_form-' + i + '-account').val('').parent().hide()
    }

    
  }
}
for (var i = 0; i < nOptions; ++i) {
  optionsBackup[i] = $('#id_form-' + i + '-account').children()    
}
$('#id_currency').change(changeCurrency)
$('#id_account').change(summary)

loadStep2()
summary()

