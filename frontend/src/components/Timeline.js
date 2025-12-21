/**
 * 时间轴组件 (使用Echarts)
 */
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';

const Timeline = ({ timeline }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const [chartHeight, setChartHeight] = useState(400);

  // 响应式高度处理
  useEffect(() => {
    const updateHeight = () => {
      setChartHeight(window.innerWidth <= 768 ? 300 : 400);
    };
    
    updateHeight();
    window.addEventListener('resize', updateHeight);
    
    return () => {
      window.removeEventListener('resize', updateHeight);
    };
  }, []);

  useEffect(() => {
    if (!timeline || !timeline.events || timeline.events.length === 0) {
      return;
    }

    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    chartInstance.current = echarts.init(chartRef.current);

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `
            <div>
              <strong>${params.data.date}</strong><br/>
              <strong>${params.data.title}</strong><br/>
              ${params.data.description}
            </div>
          `;
        }
      },
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        show: false
      },
      series: [{
        type: 'line',
        data: timeline.events.map(event => ({
          value: [event.date, 0],
          date: event.date,
          title: event.title,
          description: event.description
        })),
        symbol: 'circle',
        symbolSize: 10,
        lineStyle: {
          color: '#5470c6'
        },
        itemStyle: {
          color: '#5470c6'
        }
      }]
    };

    chartInstance.current.setOption(option);

    const handleResize = () => {
      if (chartInstance.current) {
        chartInstance.current.resize();
      }
    };

    // 监听窗口大小变化，适配移动端
    window.addEventListener('resize', handleResize);
    
    // 初始化时也触发一次resize，确保图表正确渲染
    setTimeout(() => {
      handleResize();
    }, 100);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
    };
  }, [timeline]);

  if (!timeline || !timeline.events || timeline.events.length === 0) {
    return <div className="timeline-empty">暂无时间轴数据</div>;
  }

  return (
    <div className="timeline-container">
      <div 
        ref={chartRef} 
        style={{ 
          width: '100%', 
          height: `${chartHeight}px`
        }} 
      />
    </div>
  );
};

export default Timeline;

