part of 'analytics_summary_screen.dart';

class _AttendanceChart extends StatelessWidget {
  final List<AnalyticsSeriesPoint> series;

  const _AttendanceChart({required this.series});

  @override
  Widget build(BuildContext context) {
    if (series.isEmpty) {
      return const Center(child: Text('—'));
    }

    final maxValue = series
        .map((item) => item.value)
        .fold<double>(0, (a, b) => a > b ? a : b);

    return LineChart(
      LineChartData(
        minY: 0,
        maxY: (maxValue * 1.2).clamp(1, 100),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 32),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= series.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    series[index].label,
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: series
                .asMap()
                .entries
                .map((entry) => FlSpot(entry.key.toDouble(), entry.value.value))
                .toList(),
            isCurved: true,
            color: Colors.blue,
            barWidth: 3,
            dotData: const FlDotData(show: true),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.blue.withAlpha(24),
            ),
          ),
        ],
      ),
    );
  }
}

class _DistributionChart extends StatelessWidget {
  final List<AnalyticsBucket> buckets;
  final Color color;

  const _DistributionChart({
    required this.buckets,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    if (buckets.isEmpty) {
      return const Center(child: Text('—'));
    }

    final maxValue = buckets
        .map((item) => item.count.toDouble())
        .fold<double>(0, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        maxY: (maxValue * 1.2).clamp(1, double.infinity),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 28),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= buckets.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    buckets[index].label,
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        barGroups: buckets
            .asMap()
            .entries
            .map(
              (entry) => BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: entry.value.count.toDouble(),
                    color: color,
                    width: 18,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(6),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}

class _WaterfallChart extends StatelessWidget {
  final List<double> values;
  final List<String> labels;

  const _WaterfallChart({
    required this.values,
    required this.labels,
  });

  @override
  Widget build(BuildContext context) {
    final colors = [Colors.indigo, Colors.green, Colors.orange];
    final maxValue = values.fold<double>(0, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        maxY: (maxValue * 1.2).clamp(1, double.infinity),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 32),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= labels.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    labels[index],
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        barGroups: values
            .asMap()
            .entries
            .map(
              (entry) => BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: entry.value,
                    color: colors[entry.key % colors.length],
                    width: 18,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(6),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}

class _FunnelChartCard extends StatelessWidget {
  final List<FunnelStage> funnel;

  const _FunnelChartCard({required this.funnel});

  @override
  Widget build(BuildContext context) {
    if (funnel.isEmpty) {
      return const Center(child: Text('—'));
    }

    final maxValue = funnel
        .map((item) => item.value.toDouble())
        .fold<double>(0, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        maxY: (maxValue * 1.2).clamp(1, double.infinity),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 32),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= funnel.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    funnel[index].label,
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        barGroups: funnel
            .asMap()
            .entries
            .map(
              (entry) => BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: entry.value.value.toDouble(),
                    color: Colors.deepPurple,
                    width: 18,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(6),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}
