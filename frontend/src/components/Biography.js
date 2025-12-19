/**
 * 个人传记渲染组件
 */
import React from 'react';
import Timeline from './Timeline';

const Biography = ({ biography }) => {
  if (!biography) {
    return null;
  }

  return (
    <div className="biography">
      <header className="biography-header">
        <h2>{biography.person_name}</h2>
      </header>
      
      <div className="biography-content">
        <div className="biography-text">
          {biography.content.split('\n').map((paragraph, idx) => (
            <p key={idx}>{paragraph}</p>
          ))}
        </div>
        
        {biography.timeline && (
          <div className="biography-timeline">
            <h3>时间轴</h3>
            <Timeline timeline={biography.timeline} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Biography;

