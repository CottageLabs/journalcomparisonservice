

function checkOther(elem) {
    const other = elem.form.elements[elem.name + '_other'];

    if(elem.getAttribute('data-abbreviation') && elem.getAttribute('data-abbreviation').toLowerCase() == 'inasp') {
        if(elem.checked)    {
            $('#which-platform').fadeIn();
        }
        else    {
            $('#which-platform').fadeOut();
            // Whenever hiding the journals, uncheck them to avoid submitting them
            elem.form.elements['inasp_journals'].forEach((c) => c.checked = false)

        }
    }

    if(elem.getAttribute('data-abbreviation') && elem.getAttribute('data-abbreviation').toLowerCase() === 'other')  {
        other.disabled = !other.disabled;
    }
    else if(elem.type === 'radio') {
        other.disabled = true;
    }

    if(other.disabled) {
        other.value = '';
    }
}

function checkTradeBodies(radio) {
    if(radio.value === 'True')  {
        $('#which-trade-body').fadeIn();
        $("html, body").animate({ scrollTop: $(document).height() }, 10);
    }
    else  {
        $('#which-trade-body').fadeOut();
        // Whenever hiding the journals, uncheck them to avoid submitting them
        radio.form.elements['trade_bodies'].forEach((c) => c.checked = false)
        radio.form.elements['trade_bodies_other'].value = "";
        radio.form.elements['trade_bodies_other'].disabled = true;
        $('#which-trade-body > span').empty();
    }
}

function ready(callback){
    // in case the document is already rendered
    if (document.readyState!='loading') callback();
    // modern browsers
    else if (document.addEventListener) document.addEventListener('DOMContentLoaded', callback);
    // IE <= 8
    else document.attachEvent('onreadystatechange', function(){
        if (document.readyState=='complete') callback();
    });
}

ready(function(){
    let form = document.getElementById('publisher_form');
    if(form)    {
        const disabled = ['services', 'trade_bodies'];

        disabled.forEach(function(element_name) {
            let set = form.elements[element_name];
            let other = form.elements[element_name + "_other"];

            if(set) {
                set.forEach(function(element) {
                    if(element.checked && element.getAttribute('data-abbreviation').toLowerCase() === 'other') {
                        other.disabled = false;
                    }else {
                        other.disabled = true;
                    }
                });
            }

            // This snippet loops over the services elements and displays the which-platform
            // div if the INASP checkbox is is checked. This can happen if form is invalid.
            if(form.elements['services'])   {
                form.elements['services'].forEach((c) =>   {
                    if(c.checked && c.getAttribute('data-abbreviation').toLowerCase() === 'inasp') {
                        document.getElementById('which-platform').style.display = 'block';
                    }
                });
            }

            var trade_body = form.elements['member_of_publisher_trade_body'];
            if(trade_body && trade_body.value === 'True')  {
                document.getElementById('which-trade-body').style.display = 'block';
            }

        });

    }

});