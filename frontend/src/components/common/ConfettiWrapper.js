import React from 'react';

// Este componente serve como um wrapper para o react-confetti
// para evitar problemas de importação com jsx-runtime
const ConfettiWrapper = ({ active = true, ...props }) => {
    const [Confetti, setConfetti] = React.useState(null);

    React.useEffect(() => {
        // Importação dinâmica para evitar problemas durante a compilação
        import('react-confetti').then(module => {
            setConfetti(() => module.default);
        }).catch(err => {
            console.error('Erro ao carregar o componente Confetti:', err);
        });
    }, []);

    if (!active || !Confetti) return null;

    return <Confetti {...props} />;
};

export default ConfettiWrapper;