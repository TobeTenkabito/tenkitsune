import React, { useState, useEffect } from 'react';
import axios from 'axios';

// API Base URL
const API_BASE_URL = 'http://127.0.0.1:8000';

// 通用 API 请求函数
async function apiRequest(path, method, data = null) {
  try {
    const response = await axios({
      method,
      url: `${API_BASE_URL}${path}`,
      data,
    });
    return response.data;
  } catch (error) {
    console.error("网络错误:", error);
    // 检查是否有详细的错误响应
    const errorMessage = error.response ? error.response.data.detail : "无法连接到游戏服务器。请确保后端已启动。";
    return { error: errorMessage };
  }
}

// 标题界面组件
const TitleScreen = ({ onChoice }) => {
  const [title, setTitle] = useState('');
  const [options, setOptions] = useState([]);

  useEffect(() => {
    async function fetchTitle() {
      const data = await apiRequest('/game/title', 'GET');
      if (data && !data.error) {
        setTitle(data.title);
        setOptions(data.options);
      }
    }
    fetchTitle();
  }, []);

  return (
    <div className="text-center">
      <h2 className="text-3xl font-bold mb-6">{title}</h2>
      <div>
        {options.map(option => (
          <button
            key={option.id}
            className="btn btn-primary btn-option"
            onClick={() => onChoice(option.id)}
          >
            {option.text}
          </button>
        ))}
      </div>
    </div>
  );
};

// 存档选择界面组件
const SaveSlotScreen = ({ saveSlots, onSelect }) => {
  const [selectedSlot, setSelectedSlot] = useState(null);

  return (
    <div className="text-center">
      <h2 className="text-2xl font-bold mb-4">选择存档位</h2>
      <div className="mb-4">
        {saveSlots.map(slot => (
          <p key={slot.id} className="py-2">{slot.text}</p>
        ))}
      </div>
      <input
        type="number"
        className="w-full px-4 py-2 border rounded-md mb-4"
        placeholder="请输入存档编号 (1-5)"
        min="1"
        max="5"
        onChange={(e) => setSelectedSlot(parseInt(e.target.value))}
      />
      <button
        className="btn btn-primary w-full"
        onClick={() => onSelect(selectedSlot)}
      >
        确认
      </button>
    </div>
  );
};

// 主游戏界面组件
const MainGameScreen = ({ playerInfo, onAction }) => {
  const { player, map, actions } = playerInfo;
  return (
    <div>
      <h2 className="text-3xl font-bold text-center mb-4">主界面</h2>
      <div className="bg-gray-100 p-4 rounded-md mb-4">
        <h3 className="font-bold">玩家信息</h3>
        <p>姓名: {player.name}</p>
        <p>等级: {player.level}</p>
        <p>血量: {player.hp} / {player.max_hp}</p>
        <p>攻击力: {player.attack}</p>
      </div>
      <div className="bg-gray-100 p-4 rounded-md mb-6">
        <h3 className="font-bold">当前位置</h3>
        <p>地图: {map.name}</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {actions.map(action => (
          <button
            key={action.id}
            className="btn btn-primary btn-option"
            onClick={() => onAction(action.id)}
          >
            {action.text}
          </button>
        ))}
      </div>
    </div>
  );
};

// 错误信息显示组件
const ErrorScreen = ({ message, onRetry }) => (
  <div className="text-center">
    <div className="text-red-500 font-bold mb-4">{message}</div>
    <button className="btn btn-primary w-full" onClick={onRetry}>返回主界面</button>
  </div>
);

// 主应用组件
const App = () => {
  const [screen, setScreen] = useState('title');
  const [playerData, setPlayerData] = useState(null);
  const [saveSlots, setSaveSlots] = useState([]);
  const [error, setError] = useState(null);

  const processTitleChoice = async (choice) => {
    const data = await apiRequest('/game/title/choice', 'POST', { choice });
    if (data.error) {
      setError(data.error);
    } else if (data.next_screen === 'choose_slot' || data.next_screen === 'load') {
      setScreen('choose_slot');
      setSaveSlots(data.save_slots);
    } else if (data.status === 'game_ended') {
      setError(data.message);
    }
  };

  const processSaveSlotChoice = async (slotNumber) => {
    if (!slotNumber) {
      setError("请输入有效的存档编号。");
      return;
    }
    const data = await apiRequest('/game/start_new', 'POST', { slot_number: slotNumber });
    if (data.error) {
      setError(data.error);
    } else {
      setPlayerData(data);
      setScreen('main');
    }
  };

  const processGameAction = async (actionId) => {
    const data = await apiRequest('/game/action', 'POST', { action_id: actionId });
    if (data.error) {
      setError(data.error);
    } else if (data.status === 'game_ended') {
      setError(data.message);
      setPlayerData(null);
    } else {
      setPlayerData(data);
    }
  };

  const retry = () => {
    setError(null);
    setScreen('title');
  };

  const renderContent = () => {
    if (error) {
      return <ErrorScreen message={error} onRetry={retry} />;
    }
    switch (screen) {
      case 'title':
        return <TitleScreen onChoice={processTitleChoice} />;
      case 'choose_slot':
        return <SaveSlotScreen saveSlots={saveSlots} onSelect={processSaveSlotChoice} />;
      case 'main':
        return <MainGameScreen playerInfo={playerData} onAction={processGameAction} />;
      default:
        return <ErrorScreen message="未知的游戏状态。" onRetry={retry} />;
    }
  };

  return (
    <div className="game-container">
      {renderContent()}
    </div>
  );
};

export default App;
