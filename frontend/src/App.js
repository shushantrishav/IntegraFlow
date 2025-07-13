import { IntegrationForm } from './integration-form';

function App() {
  return (
    // The main container styling is now handled by the IntegrationForm's outermost Box
    // No direct styling needed here for the overall app background, as it's in index.css body
    <div>
      <IntegrationForm />
    </div>
  );
}

export default App;
