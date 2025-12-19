/**
 * 主页组件
 */
import React, { useState } from 'react';
import InputForm from '../components/InputForm';
import ChatInterface from '../components/ChatInterface';
import FamilyReport from '../components/FamilyReport';
import { createUser, generateReport } from '../services/api';

const Home = () => {
  const [step, setStep] = useState('input'); // 'input', 'chat', 'report'
  const [userData, setUserData] = useState(null);
  const [report, setReport] = useState(null);

  const handleFormSubmit = async (formData) => {
    try {
      const user = await createUser(formData);
      setUserData(user);
      setStep('chat');
    } catch (error) {
      console.error('创建用户失败:', error);
      alert('创建用户失败，请重试');
    }
  };

  const handleGenerateReport = async () => {
    if (!userData) return;
    
    try {
      const reportData = await generateReport(userData.id);
      setReport(reportData);
      setStep('report');
    } catch (error) {
      console.error('生成报告失败:', error);
      alert('生成报告失败，请重试');
    }
  };

  return (
    <div className="home-page">
      <header className="app-header">
        <h1>RootJourney</h1>
        <p>探索您的家族历史</p>
      </header>

      <main className="app-main">
        {step === 'input' && (
          <section className="input-section">
            <h2>开始您的家族探索之旅</h2>
            <InputForm onSubmit={handleFormSubmit} />
          </section>
        )}

        {step === 'chat' && (
          <section className="chat-section">
            <h2>与AI对话，了解更多信息</h2>
            <ChatInterface context={userData} />
            <button onClick={handleGenerateReport} className="generate-button">
              生成家族报告
            </button>
          </section>
        )}

        {step === 'report' && (
          <section className="report-section">
            <FamilyReport report={report} />
          </section>
        )}
      </main>
    </div>
  );
};

export default Home;

