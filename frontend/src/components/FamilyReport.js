/**
 * 家族报告渲染组件
 */
import React from 'react';
import Biography from './Biography';
import Timeline from './Timeline';

const FamilyReport = ({ report }) => {
  if (!report) {
    return <div className="loading">加载中...</div>;
  }

  return (
    <div className="family-report">
      <header className="report-header">
        <h1>{report.title}</h1>
        <p className="report-summary">{report.summary}</p>
        <p className="report-date">生成时间: {report.generated_at}</p>
      </header>

      <section className="biographies-section">
        <h2>家族成员传记</h2>
        {report.biographies.map((biography, idx) => (
          <Biography key={idx} biography={biography} />
        ))}
      </section>

      <section className="family-tree-section">
        <h2>家族图谱</h2>
        <div className="family-tree-container">
          {/* TODO: 渲染家族树可视化 */}
          <p>家族树可视化将在这里显示</p>
        </div>
      </section>
    </div>
  );
};

export default FamilyReport;

