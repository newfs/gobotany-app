function jquery_autocomplete(name, ac_url, force_selection) {
    $(document).ready(function () {
        var input = $('#id_' + name);
        var hidden_input = $('#id_hidden_' + name);
        input.autocomplete(ac_url, {
            limit: 10,
            matchSubset: false,
            dataType: 'json',
            parse: function(data) {
                var parsed = [];
                for (var i in data) {
                    row = {
                        data: data[i][1]+'|'+data[i][0],
                        value: data[i][0],
                        result: data[i][1]
                    };
                    parsed[parsed.length] = row;
                }
                return parsed;
            },    
            formatItem: function(data, i, total) {
                return data.split('|')[0];
            }
        });
        input.result(function(event, data, formatted) {
            hidden_input.val(data.split('|')[1]);
        });
        form = $("form:first");
        form.submit(function() {
            if (hidden_input.val() != input.val() && !force_selection) {
                hidden_input.val(input.val());
            }
        });
    });
}

autocomplete = jquery_autocomplete;
