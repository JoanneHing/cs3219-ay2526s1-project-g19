import MatchingForm from "../components/matchingService/matchingForm";
import CancelConfirmation from "../components/matchingService/CancelConfirmation";
import MatchFound from "../components/matchingService/MatchFound";
import MatchNotFound from "../components/matchingService/MatchNotFound";

const MatchingPage = () => {
    return (
        <div className="flex w-full h-screen">
            <div className="flex items-center justify-center w-full">
                <MatchingForm />
                <MatchNotFound />
            </div>
        </div>
    );
};
export default MatchingPage;
