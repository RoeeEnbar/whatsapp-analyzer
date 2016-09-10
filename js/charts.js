function emoji_histogram(html_id, name, emojis, limit) {
    var labels = [];
    var count = [];
    limit = Math.min(limit, emojis.length);
    for (var i=0; i < limit; i++) {
        labels.push(emojis[i][0]);
        count.push(emojis[i][1]);
    }
    $(html_id).highcharts({
        chart: {
            type: 'bar'
        },
        title: {
            text: 'Most used emojis by ' + name
        },
        xAxis: {
            categories: labels,
            tickLength: 0,
            labels: {
                align: 'center',
                step: 1,
                padding: 3,
                y: 9,
                style: {
                    fontSize: 24,
                }
            },
            title: {
                text: null
            }
        },
        yAxis: {
            min: 0,
            gridLineWidth: 0,
            title: {
                enabled: false
            },
            labels: {
                overflow: 'justify',
                enabled: false
            }
        },
        plotOptions: {
            bar: {
                dataLabels: {
                    enabled: true
                }
            }
        },

        credits: {
            enabled: false
        },
        series: [{
            showInLegend: false,
            data: count
        }]
    });
};
