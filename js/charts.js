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

function conversation_starters_plot(data) {
    $("#conversation_starters").highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            type: 'pie'
        },
        title: {
            text: 'Who started the conversation?'
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                    style: {
                        color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                    }
                }
            }
        },
        series: [{
            name: 'names',
            colorByPoint: true,
            data: data
        }]
    });
};
