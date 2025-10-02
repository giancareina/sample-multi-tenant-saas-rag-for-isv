// App.tsx
import { BrowserRouter, Route, Routes } from "react-router-dom";
import './App.css';
import { Authenticator } from '@aws-amplify/ui-react'
import '@aws-amplify/ui-react/styles.css';
import Header from './components/Header';
import { UploadContainer } from "./features/upload/UploadContainer";
import { DocumentListContainer } from "./features/documents/DocumentListContainer";
import Footer from "./components/Footer";
import { ChatContainer } from "./features/chat/ChatContainer";
import { UsageContainer } from "./features/usage/UsageContainer";
import { configureAmplify } from './config/amplify';

configureAmplify();

function App() {
  return (
    <BrowserRouter>
      <Authenticator>
        {() => (
          <div className="h-screen flex flex-col bg-gray-50">
            <Header />
            <main className="flex-1 overflow-hidden relative">
              <div className="h-full">
                <Routes>
                  <Route path="/" element={<ChatContainer />} />
                  <Route path="/upload" element={<UploadContainer />} />
                  <Route path="/doc" element={<DocumentListContainer />} />
                  <Route path="/usage" element={<UsageContainer />} />
                </Routes>
              </div>
            </main>
            <Footer />
          </div>
        )}
      </Authenticator>
    </BrowserRouter>
  );
}

export default App;
