// prepopulate boxes to eliminate FF weirdness

$( document ).ready(function() {
	$("select").each(function(){
		$(this).wrap("<div class='select_button'></div>");
		$(this).addClass('init');
	});
}); 

var hide_timer = null;

var addRippleEffect = function (e) {
	if ($( "body" ).hasClass( "no_forms" ) || !$( "body" ).hasClass( "material" ) ){
		return false;
	} else {
		var target = e.target;
		//handle select boxes 
		if (target.tagName.toLowerCase() == 'select') {
			var rect = target.getBoundingClientRect();
			var ripple = $(target).hasClass('init');
			if (! $(target).closest(".select_button").length) {
				$(target).wrap("<div class='select_button'></div>");
				$(target).addClass('init');
			}
			if (! $(target).next('.ripple').length) {
				ripple = document.createElement('span');
				ripple.className = 'ripple';
				ripple.style.height = ripple.style.width = Math.max(rect.width, rect.height) + 'px';
				$(target).parent().append(ripple);
			}
			var ripple = $(target).next('.ripple')[0];
		} else { 
			var ripple = target.querySelector('.ripple');
			var rect = target.getBoundingClientRect();
			if (!ripple) {
				ripple = document.createElement('span');
				ripple.className = 'ripple';
				ripple.style.height = ripple.style.width = Math.max(rect.width, rect.height) + 'px';
				target.appendChild(ripple);
			}
		}
		$(ripple).removeClass("show");
		if (hide_timer) {clearTimeout(hide_timer);}
		var targetOffset = $(target).offset(); 
		var top = e.pageY - targetOffset.top - ripple.offsetHeight / 2;
		var left = e.pageX - targetOffset.left - ripple.offsetWidth / 2;
		$(ripple).css("top", top + "px");
		$(ripple).css("left", left + "px");
		$(ripple).addClass("show");
		hide_timer = setTimeout(function(){$(ripple).removeClass("show");}, 500);
		return false;
	}
}


$('button[type!=submit][type!=hidden], .input.select select, .add_ripple').click(addRippleEffect);


// handle form elements


+function ($) {
	'use strict';

	function setInputValue() {
		var val = $(this).val();
		val ? $(this).attr('value', val) : $(this).removeAttr('value');
	}

	function setTextareaValue() {
		$(this).text($(this).val());
	}

	$(document).on('change', ".input input[type='text'], .input input[type='email'], .input input[type='password']", setInputValue);
	$(document).on('change', ".input textarea", setTextareaValue);

	$.fn.refresh = setInputValue;

	$(window).on('load', function() {
		var isFirefox = typeof InstallTrigger !== 'undefined';
		var isIE = /*@cc_on!@*/false || !!document.documentMode;
		if (isFirefox || isIE) {
			$(".input input[type='text']:not([value]), .input input[type='email']:not([value]), .input input[type='password']:not([value])")
			.filter(function() { return $(this).val();}).refresh();
		}
	});

}($);
